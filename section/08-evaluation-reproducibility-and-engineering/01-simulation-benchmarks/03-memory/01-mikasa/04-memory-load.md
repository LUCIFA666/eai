# 记忆负载机制

这些任务依赖记忆，是因为部分可观测是在环境里刻意造出来的：线索只在有限的窗口里出现，随后被移出视野或被打乱，到该行动时当前一帧已经不含答案。环境反复用到三种手法：按脚本在不同阶段隐藏或搬动物体、在行动阶段随机重排布局、并且逐个 episode 随机各阶段的长度。源码都在 `mikasa_robo_suite/vla/memory_envs/`。下面先说清这套设计要堵住的捷径，再按机制分组、用代表环境说明。

## 防捷径的设计

这些机制服务同一个目标：让当前观测按构造就不足以决策，同时堵住不靠记忆也能蒙对的捷径。三种随机化和难度阶梯各堵一类：

- 行动阶段随机重排布局，堵住用位置替代内容的捷径。cue 阶段与行动阶段的物体排布不同，记住位置没有用，只有记住颜色、形状、身份这些真正的线索才能对上。
- 各阶段长度逐 episode 随机，堵住按固定步数触发动作的捷径。策略记不住第几步该动手，必须自己检测线索消失、场景切换这类事件。
- 数量档和 Long 变体沿难度阶梯加码，堵住靠少量候选或短间隔蒙对的捷径。候选越多、间隔越长，越逼近真正的长时保持，越难靠运气过关。
- `oracle_info` 这类含正确答案的特权信息只留给 oracle 与数据采集，从 VLA 观测里剥掉，策略拿不到直接答案。

正因为这些捷径被堵住，一个只看当前帧的反应式策略在这些任务上无从下手，唯一的通路是把历史信息真正保留、更新并在后续用上。

## 三段式：以 RememberColor 为例

RememberColor 的一个 episode 分成 cue、memory、action 三段，边界由两个随机步数决定：每次 reset 时从 `CUE_PHASE_STEPS`、`EMPTY_PHASE_STEPS` 各采一个值，cue 段结束于 `cue_steps`，memory 段结束于 `cue_steps + empty_steps`。`evaluate` 里据此算出各阶段掩码，并把非动作阶段的方块抬到视野外：

```python
# remember_color_vla.py，evaluate()
cue_end   = self.cue_steps_per_env
empty_end = cue_end + self.empty_steps_per_env
empty_mask = (elapsed_steps >= cue_end) & (elapsed_steps < empty_end)
manip_mask = elapsed_steps >= empty_end
hidden_phase_mask = ~manip_mask          # cue 与 memory 两段都属隐藏期

for key in self.color_dict:
    hidden_shapes_poses[key][hidden_phase_mask, 2] = 1000   # 把方块抬到 z=1000，移出相机视野
```

cue 阶段只把目标颜色的方块显示在桌面中央，其余移出视野；memory 阶段所有方块都被移走，画面空无一物；action 阶段所有候选方块重新出现、位置随机重排，策略要伸到颜色与线索相同的那个。隐藏或刚出现时还会把线速度、角速度清零。因为 action 阶段的排布与 cue 阶段不同，位置不携带答案，只有颜色身份能对应到正确方块。

成功条件是末端伸到正确方块、距离在 `GOAL_THRESH`（0.05）以内且机器人静止；正确答案（目标颜色下标）放在 `oracle_info` 里，是特权信息，VLA 观测里被剥掉。达成成功不会立即结束 episode，整体成功由 `success_once` 锁存。难度与时长写在注册常量里，Long 变体只把相位拉长、任务不变：

```python
@register_env("RememberColor3-VLA-v0", max_episode_steps=25)
class RememberColor3VLAEnv(RememberColorVLABaseEnv):
    COLORS = 3
    CUE_PHASE_STEPS = [1, 5]
    EMPTY_PHASE_STEPS = [1, 5]

@register_env("RememberColor3-Long-VLA-v0", max_episode_steps=600)
class RememberColor3LongVLAEnv(RememberColorVLABaseEnv):
    COLORS = 3
    CUE_PHASE_STEPS = [10, 100]
    EMPTY_PHASE_STEPS = [50, 450]
```

## 持续追踪：以 ShellGameShuffle 为例

不是所有任务都是先看后做。ShellGameShuffleTouch 要在整段过程里持续更新对目标的估计：cue 阶段把三个杯子抬起、露出球所在的槽位；shuffle 阶段杯子落下并按随机的若干次两两交换来回移动，球被抬到高处藏起，每交换一次藏球的槽位就变一次；action 阶段杯子停下，策略要触碰此刻藏球的杯子。没有一个固定位置可记，对藏球位置的估计要跟着每次交换一路更新。成功除了触到正确杯子（`GOAL_THRESH` 0.08）且静止，还要求没有碰移其他杯子（位移在 0.05 以内）。标准与 Long 变体的差别在相位常量与交换次数：

```python
@register_env("ShellGameShuffleTouch-VLA-v0", max_episode_steps=60, asset_download_ids=["ycb"])
class ShellGameShuffleTouchVLAEnv(ShellGameShuffleTouchVLABaseEnv):
    CUE_PHASE_STEPS = [1, 5]
    SHUFFLE_PHASE_STEPS = [20, 35]
    NUM_SWAPS = [2, 4]

@register_env("ShellGameShuffleTouch-Long-VLA-v0", max_episode_steps=600, asset_download_ids=["ycb"])
class ShellGameShuffleTouchLongVLAEnv(ShellGameShuffleTouchVLABaseEnv):
    CUE_PHASE_STEPS = [10, 100]
    SHUFFLE_PHASE_STEPS = [100, 400]
    NUM_SWAPS = [5, 15]
```

## 计数与时序：Blink 与 Timed

Temporal 类不给一个可记的静态线索，而是让信息随时间累积。BlinkCountButtonPress 用一盏蓝灯闪烁，闪烁的次数、每次亮灭时长都逐 episode 随机采样，`cue_steps` 由这些时长累加而成；cue 阶段一盏相位灯显示红色、action 阶段变绿。数完之后要按相同次数的红按钮，每次按压必须按下再抬起构成一个完整循环才计一次（按压深度达到 `BUTTON_CAP_TRAVEL*0.35`、随后抬起 `REQUIRED_LIFT_HEIGHT=0.1`），按多了直接判失败，最后按黑色确认按钮提交。`oracle_info` 存的是真实闪烁次数 `target_blinks`。

TimedTransfer 更纯粹地考察对步数的内部计数：一盏白灯在 `signal_step` 变绿，策略要从那一刻起数步，恰好在第 N 步（N 即 `DELAY_STEPS`）把蓝方块从绿盘移到红盘。成功窗口只有 N 的正负 `TOLERANCE_FRAC=0.05`，早放晚放都算失败。标准变体的 `DELAY_STEPS` 为 100 / 150 / 200（Easy / Medium / Hard），Long 变体拉到 300 / 500 / 1000。`oracle_info` 存 `DELAY_STEPS`。

## 意图与过程：Gather 与 Trace

Prospective 类要在做别的事时把一个意图挂着。GatherAndRecall 要把所有方块搬到圆盘上，当放上圆盘的方块数达到一个随机触发阈值时，一盏灯短暂闪一种颜色（`FLASH_DURATION_STEPS=[8,14]`）；确认按钮只有在所有方块都放好后才能按，按下与闪光颜色匹配的按钮才成功，按错即失败。也就是说，要记住的颜色出现在中途的搬运过程里，而用到它的动作在很久以后。`oracle_info` 存闪光颜色下标 `flash_color`。

Procedural 类要复现一段运动轨迹。TraceShape 在 demo 阶段让一个红方块沿 `NUM_WAYPOINTS=64` 个路点描出一个形状（相位灯红色），action 阶段灯变绿、红方块被藏起（z 抬到 1000），策略要用绿方块访遍轨迹上采样出的 `NUM_CHECKPOINTS=12` 个 checkpoint（每个 `CHECKPOINT_THRESH=0.035`）并回到起点闭合轮廓。TraceShapeSeq 把多个形状连成序列、逐个复现后再按提交按钮。`oracle_info` 存形状 ID（TraceShapeSeq 还把整条形状序列同时写进 `task_cue`）。

## 多阶段验证：Batteries 的三阶段状态机

BatteriesChecker 没有时间相位，而是每个 env 跑一个三阶段状态机 `STAGE_INSERT → STAGE_RETURN → STAGE_CONFIRM`：

```python
# batteries_checker_hard_vla.py
STAGE_INSERT = 0
STAGE_RETURN = 1
STAGE_CONFIRM = 2
```

插入阶段把电池放进插座（插入判定 `SOCKET_INSERT_XY_TOL=0.010`、`SOCKET_INSERT_Z_TOL=0.025`），如果是可用电池，黄灯亮起并维持 `LAMP_AFTERGLOW_STEPS=7` 步作为反馈；Hard 变体还要在返回阶段把电池放回它原来的槽位，Easy 变体则由环境自动归位。全部检验完、可用电池数达标、且都归位后，在确认阶段按按钮提交才成功。`oracle_info` 存可用电池的下标。这里的记忆负担是记住哪些电池已测、结果如何、哪些还没测。

## 缺失、集合与顺序：FindImposter 与 colors

FindImposter 定义目标的方式是缺失：cue 阶段只展示除某个颜色以外的方块（缺的那个被抬到 z=1000），empty 阶段全部藏起，manip 阶段所有方块出现且位置被打乱，要触碰那个之前缺席的颜色。`oracle_info` 存缺席颜色下标 `imposter_key`。

BunchOfColors、SeqOfColors、ChainOfColors 共用同一套布局：cue 展示一组目标颜色（BunchOfColors 同时展示、SeqOfColors 与 ChainOfColors 逐个展示），empty 阶段全部藏到 `BUTTON_HIDDEN_Z=1000`，之后 9 个方块随机重排出现，要触碰全部目标再按中心按钮，且不能碰移其他方块（位移超过 `MAX_ALLOWED_CUBE_DISPLACEMENT=0.06` 使成功作废）。区别在判定：BunchOfColors 和 SeqOfColors 按集合判定、顺序不限，ChainOfColors 要求触碰顺序与展示顺序一致，乱序即无法成功。

## 共同的设计手法

上面这些环境共享一批实现约定：

- 遮挡靠把物体抬到 z=1000（`HEIGHT_OFFSET` / `BUTTON_HIDDEN_Z`）移出视野，灯用双灯泡在亮灭位置间切换并配 `emission_scale` 提亮，线索是干净地出现和消失。
- action 阶段随机重排布局、各阶段长度逐 episode 随机，避免策略拿位置或固定步数当真正线索的替身。
- 带按钮的任务共用一套去抖常量：`BUTTON_CAP_TRAVEL=0.014`、按下阈值比例 `0.35`、抬起确认高度 `REQUIRED_LIFT_HEIGHT=0.1`，避免一次接触被误计多次。
- 短程且属课程式的变体（ShellGame*、非 Long 的 RememberColor/Shape、FindImposter* 等）套 `CurriculumPhaseNoopActionWrapper`，在 `elapsed < cue_steps + empty_steps` 期间把动作清零，强制策略在 cue 与 memory 阶段不动；Long 变体不套这个 wrapper。
- `oracle_info` 一律作为特权标签服务 oracle 与数据采集，不进入 VLA 观测；成功判定基本都限定在 action 阶段。
- `normalized_dense` 奖励等于 dense 除以该任务的成功奖励值，而成功奖励值随任务而异（如 ShellGameTouch、FindImposter 为 3.0，Blink、Timed、Intercept、TakeItBack 为 30.0，Batteries、TraceShapeSeq 为 40.0，Gather 为 50.0，Rotate 为 100.0，颜色集合类为 400.0），归一化后各任务量纲可比。

## 导航

- 返回上级：[MIKASA-Robo-VLA](../01-mikasa.md)
- 上一节：[任务目录](03-task-catalogue.md)
- 下一节：[难度与时间跨度](05-difficulty-and-horizon.md)
