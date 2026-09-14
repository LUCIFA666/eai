# 记忆负载机制

RoboMME 的任务都被设计成非马尔可夫：决定动作所需的信息在决策时已经不在当前帧里。环境靠两套东西把这件事做实，一套是判定任务是否完成的分阶段验证骨架，一套是把物体隐藏、移动、交换的状态操作原语。源码在 `src/robomme/robomme_env/`，通用逻辑集中在 `utils/subgoal_evaluate_func.py` 和 `utils/statechange.py`。

## 分阶段验证:判定骨架

每个任务在 `evaluate()` 里构建一个有序的 `self.task_list`，每一项是一个子阶段，含判定函数 `func`、失败函数 `failure_func`、是否属于演示阶段 `demonstration` 等字段。`sequential_task_check` 维护一个指针，逐阶段推进：先查 `failure_func`，再查 `func`，通过就前进；只有所有阶段完成且未触发失败，`evaluate()` 才置成功。

```python
# utils/subgoal_evaluate_func.py
def sequential_task_check(self, tasks, allow_subgoal_change_this_timestep):
    # 返回 (all_completed, current_task_name, task_failed, specialflag)
    # 逐阶段推进 self.timestep：failure_func 先判、func 后判
    ...
# evaluate(): successflag = all_completed and not task_failed
```

阶段判定复用一组带阈值的谓词，都在 `utils/subgoal_evaluate_func.py`：

```python
def is_obj_pickup(self, obj, goal_pos=None):
    obj_lifted = obj.pose.p[:, 2] > 0.05          # 抬离桌面
    is_grasping = self.agent.is_grasping(obj)     # 且夹爪抓住
    return obj_lifted & is_grasping

def is_bin_pickup(self, obj):
    return obj.pose.p[:, 2] > 0.15                # 容器抬起阈值更高

def is_button_pressed(self, obj):
    return get_button_depth(self, obj=obj) > 0.005   # 按钮下压深度
```

此外还有摆到目标 `is_obj_swing_onto`、连续静止若干步 `static_check`、以及针对钉子的 `is_A_pickup_notB` / `is_A_insert_notB`。因为成功要走完整条阶段链，任何一步作错或触发 `failure_func`（例如拾错物体、提前按按钮、摆动次数超限）都会让任务失败。

## 遮挡与洗牌:Permanence 的实现

Permanence 套件把目标藏起来。遮挡靠 `lift_and_drop_objects_back_to_original`：在时间窗内先把物体瞬移到远处坐标 `(10, 10, 10)` 移出视野，到窗口中点再落回原位上方。

```python
# utils/statechange.py, lift_and_drop_objects_back_to_original()
away = np.array([10.0, 10.0, 10.0])   # 窗口内移出相机视野
drop_target = cache["origin"].copy()  # 中点落回原位上方
```

洗牌靠 `swap_flat_two_lane`，把两个容器在同一平面上对向换位，用 smoothstep 平滑推进、正弦横向让道避免穿模，并同时锁住其他容器的位姿：

```python
# utils/statechange.py, swap_flat_two_lane()
alpha = (cur_step - start_step) / denom
alpha = alpha * alpha * (3.0 - 2.0 * alpha)     # smoothstep
offset = lane_offset * math.sin(math.pi * alpha)  # 横向让道
xa = ax + dx * alpha + nx * offset               # A、B 对向换位
xb = bx - dx * alpha - nx * offset
```

以 VideoUnmask 为例：三个彩色方块被藏在容器下，开头有一段 `static` 窗口（`static_check` 约 64 步）作为演示视频窗，之后要拾起盖住指定颜色方块的那个容器（`is_bin_pickup`，拾错别的容器即失败）。VideoUnmaskSwap 在此之上加入 1 到 3 次、每次约 50 步的容器交换，交换后目标容器的位置已变，要一路跟住。

## 计数:Counting 的实现

Counting 套件的次数无法从单帧读出，靠跨步累计。三种任务用三种实现：BinFill 把放进料箱的方块直接删除（瞬移到 `(10, 10, 0)`）并按颜色累加计数，成功要求各颜色计数与目标一致；SwingXTimes 在 `step()` 里用带滞回的边沿检测数摆动（进入阈值距离 0.03 / 高度 0.12，退出 0.04 / 0.3），上限 `max_swings = num_repeats*2`，超出即判 `too_many_swings` 失败；StopCube 用 `move_straight_line` 让方块自动往返，按钮有效窗口是第 stop_time 次经过目标的那一段（`move_interval*(stop_time-1)` 到 `move_interval*stop_time`），窗口外按下由 `correct_timestep` 判失败。

## 视频条件:演示半场与执行半场

Reference 与 Imitation 套件的任务把 `task_list` 分成两半。前半是演示半场，阶段标 `demonstration: True`，环境自动播放一段拾放、摆动或描绘的演示；中间插一个不记录的强重置阶段（`solve_strong_reset`）把场景复位；后半是执行半场，阶段标 `demonstration: False`，要求策略复现前半的内容。视频条件观测正是这段开头的演示帧序列。例如 VideoRepick 在演示里拾放某个方块（其间可能洗牌），执行时要重新拾起同一个方块若干次；InsertPeg 在演示里抓某根钉子的某端、从某侧插入，执行时要照做，`is_A_insert_notB` 会在抓错端或插错侧时判失败。

## 高亮:短暂线索

PickHighlight 用 `highlight_obj` 只在某段步数内（约第 10 到 100 步）给目标方块打上高亮盘，之后淡去；策略要记住哪些方块被高亮过，等标记消失后再逐个拾起，用上升沿计数确认每个目标至少被拾起一次，拾到未高亮的方块即失败。

## 导航

- 返回上级：[RoboMME](../02-robomme.md)
- 上一节：[任务目录](03-task-catalogue.md)
- 下一节：[观测与动作接口](05-observation-and-action.md)
