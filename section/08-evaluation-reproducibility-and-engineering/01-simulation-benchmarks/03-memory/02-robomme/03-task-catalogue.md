# 任务目录

RoboMME 的 16 个任务分在四个套件里，每个套件四个。下表先给总览：套件、记忆类型、平均步数（论文 Table 1）、是否视频条件、考察点。之后按套件逐个展开每个任务的机制、难度档与成功判定，难度参数取自各环境的 `config_easy/medium/hard`，判定谓词取自 `utils/subgoal_evaluate_func.py`。

| 任务 | 套件 | 记忆类型 | 平均步数 | 视频条件 | 考察点 |
|---|---|---|---|---|---|
| PickXTimes | Counting | 时间 | 538 | 否 | 计数 |
| BinFill | Counting | 时间 | 604 | 否 | 计数 |
| SwingXTimes | Counting | 时间 | 435 | 否 | 计数、摆动 |
| StopCube | Counting | 时间 | 317 | 否 | 计数、时机敏感 |
| VideoUnmask | Permanence | 空间 | 217 | 是 | 遮挡 |
| ButtonUnmask | Permanence | 空间 | 267 | 否 | 遮挡 |
| VideoUnmaskSwap | Permanence | 空间 | 348 | 是 | 遮挡、追踪 |
| ButtonUnmaskSwap | Permanence | 空间 | 400 | 否 | 遮挡、追踪 |
| PickHighlight | Reference | 对象 | 346 | 否 | 视觉指代 |
| VideoRepick | Reference | 对象 + 时间 | 687 | 是 | 动作指代、追踪、计数 |
| VideoPlaceButton | Reference | 对象 + 时间 | 974 | 是 | 语言指代、长视频、追踪 |
| VideoPlaceOrder | Reference | 对象 + 时间 | 1134 | 是 | 语言指代、长视频、追踪 |
| MoveCube | Imitation | 过程 | 394 | 是 | 接触方式、工具使用 |
| InsertPeg | Imitation | 过程 + 对象 | 479 | 是 | 精确运动 |
| PatternLock | Imitation | 过程 | 208 | 是 | 直线运动 |
| RouteStick | Imitation | 过程 | 370 | 是 | 环绕运动 |

## Counting 套件

- **PickXTimes**：把同一个目标方块拾放到目标处 `num_repeats` 次，再按按钮停止。难度按重复次数加码：easy 1 到 3、medium 换更难辨的颜色仍 1 到 3、hard 4 到 5。成功要走完 2·N 次拾放加一次按钮，中途拾到非目标方块或提前按按钮即失败。
- **BinFill**：把指定数量、指定颜色的方块放进料箱，放进即删除并按颜色累加计数，最后按按钮。难度调场上方块数（4 到 6 提到 10 到 12）、要放入的颜色数（1 提到 3）和放入数量（1 到 3 提到 3 到 5），hard 还会让无关方块周期性升降制造动态干扰。成功要求各颜色计数与目标一致。
- **SwingXTimes**：拾起方块在左右两个目标间来回摆动 `num_repeats` 次，放下后按按钮。摆动用带滞回的边沿检测计数（进入阈值距离 0.03、高度 0.12，退出 0.04、0.3），上限 `max_swings = num_repeats*2`，超出即判 `too_many_swings` 失败。
- **StopCube**：方块沿直线自动往返（`move_interval` 取 60、80 或 120），要在它第 `stop_time`（2 到 6）次经过目标的那一段按下按钮，有效窗口是 `move_interval*(stop_time-1)` 到 `move_interval*stop_time`，窗口外按下由 `correct_timestep` 判失败。

## Permanence 套件

- **VideoUnmask**：开头一段 `static` 视频窗（约 64 步）里，容器周期性升降露出又盖住底下的彩色方块；之后要拾起盖住指定颜色方块的那个容器（`is_bin_pickup`，拾错别的容器即失败）。难度调容器数（3 提到 15）和要拾起的目标数（1 提到 2）。
- **ButtonUnmask**：与 VideoUnmask 同样的遮挡机制，但没有视频窗，改为先按一次按钮触发，再拾起正确容器。
- **VideoUnmaskSwap**：在遮挡之外加入容器两两交换（1 到 3 次、每次约 50 步，用 `swap_flat_two_lane`），交换后目标容器已移位，要一路跟住。难度调容器数（3 到 4）与交换次数（1 到 2 提到 2 到 3）。
- **ButtonUnmaskSwap**：与 VideoUnmaskSwap 同样的遮挡加交换，但用两个按钮门控，要先各按一次左右按钮再拾容器。

## Reference 套件

- **PickHighlight**：目标方块只在第 10 到 100 步被高亮盘标记，标记消退后要把它们逐个拾起，用上升沿计数确认每个目标至少拾起一次，拾到未高亮的方块即失败。难度调场上方块数（3 提到 6）与要拾的高亮数（1 提到 3）。
- **VideoRepick**：演示里拾放某个方块（其间可能洗牌），执行时要重新拾起同一个方块 `num_repeats`（1 到 4）次再按按钮。easy 与 medium 是 3 个同色方块加洗牌，hard 换成 15 个混色方块、不洗牌。
- **VideoPlaceButton**：演示中在一次按钮按下前后各放置目标，执行时要把方块放到按钮按下之前或之后对应的那个目标上。难度调目标数（3 到 4）与是否洗牌（hard 开）。
- **VideoPlaceOrder**：演示里把方块依次放到一个目标子集，执行时要放到其中第 N 个被放过的目标上（序数指代）。hard 同样加入目标洗牌。

## Imitation 套件

- **MoveCube**：用演示里相同的方式把方块送到目标，方式在拾放、用夹爪推、用钩子拉三种里采样，任务链按采到的方式在 `evaluate()` 里现搭；执行半场要复现同一方式。
- **InsertPeg**：三根相同的钉子里选一根，要抓住演示里相同的那一端、从相同的一侧插入盒子（`is_A_insert_notB` 按方向判定），抓错端或插错侧即失败。
- **PatternLock**：用棒状末端在 N×N 网格上重描演示的路径，成功要求走过的按钮序列与演示 `match`，触到非预期按钮即失败。难度调网格（3×3 提到 5×5）与路径长度（2 到 4 提到 4 到 8）。
- **RouteStick**：沿演示相同的路径、相同的绕行方向（顺时针或逆时针）绕过一排障碍棒，执行时用叉乘符号判断绕行方向对错（`direction_fail`）。难度调路段数（2 到 3 提到 4 到 7）与是否允许回头。

## 语言目标

每个任务运行时通过 `info["task_goal"]` 提供一条自然语言目标，作为策略的文本条件。目标不是固定字符串，而是 `utils/task_goal.py` 的 `get_language_goal` 按任务当前的颜色、次数、难度现拼的一组等价措辞（多数任务给两到四种说法，训练时可取任一条增强语言鲁棒性），常规访问取第一条 `info["task_goal"][0]`。视频条件任务的目标都以 `watch the video carefully, then ...` 开头，把"照演示做"写进指令。各套件代表任务的模板如下（花括号是运行时代入的量）：

```text
# Counting
PickXTimes   pick up the {color} cube and place it on the target, repeating this action {word} times, then press the button to stop
BinFill      put {颜色数量短语，如 two red cubes and one blue cube} into the bin, then press the button to stop
StopCube     press the button to stop the cube just as it reaches the target for the {word} time

# Permanence
VideoUnmask  watch the video carefully, then pick up the container hiding the {color} cube
ButtonUnmask first press the button, then pick up the container hiding the {color} cube

# Reference
PickHighlight     first press the button, then pick up all highlighted cubes, finally press the button again to stop
VideoPlaceOrder   watch the video carefully, then place the {color} cube on the {num} target it was previously placed on

# Imitation
MoveCube     watch the video carefully, then move the cube to the target in the same manner as before
InsertPeg    watch the video carefully, then grasp the same end of the same peg you've picked before and insert it into the same side of the box
PatternLock  watch the video carefully, then use the stick attached to the robot to retrace the same pattern
RouteStick   watch the video carefully, then use the stick attached to the robot to navigate around the sticks on the table, following the same path
```

指令只描述目标语义，不泄露答案：遮挡任务只说"藏着某色方块的容器"，而不给容器位置；计数任务只给要数到的次数词，不标当前进度。目标里的 `{color}`、`{word}`、`{num}` 由该 episode 采样的颜色、`num2words` 次数词、序数词填入，因此同一任务在不同 episode 的指令并不相同。

逐 episode 的确切 seed 与难度记在 `src/robomme/env_metadata/{train,val,test}/` 的 per-task metadata 里。

## 导航

- 返回上级：[RoboMME](../02-robomme.md)
- 上一节：[记忆类型与套件](02-memory-suites.md)
- 下一节：[记忆负载机制](04-memory-load.md)
