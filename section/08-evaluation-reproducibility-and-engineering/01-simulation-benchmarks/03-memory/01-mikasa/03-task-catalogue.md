# 任务目录

MIKASA-Robo-VLA 由 26 个任务系列组成，每个系列通过难度档和 Long 变体展开成多个注册环境，合计 90 个。一个系列对应一个 Python 环境文件，同一系列的不同难度写在同一个文件里。环境 ID 形如 `RememberColor3-VLA-v0`，长时程变体在中间加 `-Long`，例如 `RememberColor3-Long-VLA-v0`。以 RememberColor 为例，`RememberColor{3,5,9}-VLA-v0` 加上三个 `-Long` 变体，一个系列就是 6 个环境。

## 任务系列一览

下表按机制相近的系列聚在一起。`采集来源` 指数据集轨迹的来源（PPO oracle 或运动规划 MP），部分系列的标准变体用 PPO、Long 变体用 MP，标为 PPO / MP。逐任务的完整参数在 `mikasa_robo_vla_envs.csv`。

| 任务系列 | 记忆类型 | 难度 / 变体 | horizon 分档 | 采集来源 | 任务目标 |
|---|---|---|---|---|---|
| ShellGameTouch | Spatial | 单一 | Short | PPO | 观察球藏在哪个杯子，触碰那个杯子 |
| ShellGamePush | Spatial | 单一 | Short | PPO | 观察球在哪个杯子，向前推那个杯子 |
| ShellGameShuffleTouch | Tracking | 单一 | Short / Medium | PPO / MP | 在洗牌过程中跟住球所在杯子，再触碰 |
| ShellGameColorLampTouch | Spatial | 单一 | Short | PPO | 记住杯下颜色，触碰与灯色匹配的杯子 |
| ShellGameShuffleColorLampTouch | Tracking | 单一 | Short / Medium | PPO / MP | 记住杯下颜色并在洗牌中跟住，触碰匹配灯色的杯子 |
| Intercept | Spatial | Slow / Medium / Fast | Short | PPO | 拦截滚动的球，把它偏转向目标 |
| InterceptGrab | Spatial | Slow / Medium / Fast | Short | PPO | 拦截滚动的球并抓住使其停下 |
| RotateLenient | Spatial | 正角 / 带符号角 | Short | PPO | 把 peg 旋转到指定角度 |
| RotateStrict | Spatial | 正角 / 带符号角 | Short | PPO | 旋转到指定角度，同时保持 peg 中心不动 |
| TakeItBack | Spatial | 单一 | Short | PPO | 把方块推到红色目标，变色后送回原位 |
| RememberColor | Object | 3 / 5 / 9 | Short / Medium | PPO / MP | 观察方块颜色，触碰同色的方块 |
| RememberShape | Object | 3 / 5 / 9 | Short / Medium | PPO / MP | 观察物体形状，触碰同形的物体 |
| RememberShapeAndColor | Object | 3x2 / 3x3 / 5x3 | Short / Medium | PPO / MP | 观察形状与颜色，触碰形色都相同的物体 |
| FindImposterColor | Negative | 3 / 5 / 9 | Short | PPO | 触碰颜色在此前没出现过的那个方块 |
| FindImposterShape | Negative | 3 / 5 / 9 | Short | PPO | 触碰形状在此前没出现过的那个物体 |
| FindImposterShapeAndColor | Negative | 3x2 / 3x3 / 5x3 | Short | PPO | 触碰形色组合在此前没出现过的那个物体 |
| BunchOfColors | Capacity | 3 / 5 / 7 | Medium / Long | MP | 记住一组颜色，任意顺序全部触碰再按中心按钮 |
| SeqOfColors | Capacity | 3 / 5 / 7 | Medium / Long | MP | 记住一组颜色，任意顺序全部触碰再按中心按钮 |
| ChainOfColors | Sequential | 3 / 5 / 7 | Medium / Long | MP | 记住颜色顺序，按相同顺序依次触碰再按中心按钮 |
| TraceShape | Procedural | Easy / Medium / Hard | Medium | MP | 看红方块描出形状，用绿方块描出相同形状 |
| TraceShapeSeq | Procedural | Easy / Medium / Hard | Long | MP | 看红方块描出一串形状，按顺序复现后按按钮提交 |
| BlinkCountButtonPress | Temporal | Easy / Medium / Hard | Short / Medium / Long | MP | 数蓝灯闪几次，红灯变绿后按相同次数，再按黑按钮提交 |
| TimedTransfer | Temporal | Easy / Medium / Hard | Short / Medium / Long | MP | 白灯变绿起数步，恰好在第 N 步把方块从绿盘移到红盘 |
| BatteriesCheckerEasy | Checklist | 3 / 6 | Medium / Long | MP | 逐个测电池看灯，按按钮确认可用电池 |
| BatteriesCheckerHard | Checklist | 3 / 6 | Long | MP | 同上，且每次测完要把电池放回原位 |
| GatherAndRecall | Prospective | 1 / 3 / 5 / 7 / 9 | Short / Medium / Long | MP | 把方块搬到圆盘，记住闪过的灯色，搬完按匹配颜色的按钮 |

## 语言指令

每个任务系列在环境类里定义一条固定的英文 `LANGUAGE_INSTRUCTION`，运行时通过 `info["language_instruction"]` 提供，作为 VLA 的文本条件；同一系列的不同难度与 Long 变体共用一条。指令只描述任务语义，不泄露答案（目标颜色、藏球杯子、闪光颜色等都不写进指令）。源码在 `mikasa_robo_suite/vla/memory_envs/*_vla.py`。

Object 与 Negative 系列（观察一次再作答）：

```text
RememberColor           Observe the cube's color, wait, then touch the cube of the same color.
RememberShape           Observe the object's shape, wait, then touch the object of the same shape.
RememberShapeAndColor   Observe the object's shape and color, wait, then touch the object of the same shape and color.
FindImposterColor       Observe the cubes shown, wait, then touch the cube whose color was not present before.
FindImposterShape       Observe the shapes shown, wait, then touch the object whose shape was not present before.
FindImposterShapeAndColor  Observe the objects shown, wait, then touch the object whose shape and color combination was not present before.
```

ShellGame 与拦截、返回等空间系列：

```text
ShellGameTouch                Observe which cup hides the ball, wait, then touch that cup.
ShellGamePush                 Observe which cup hides the ball, wait, then push that cup forward.
ShellGameShuffleTouch         Observe which cup hides the ball, track the cups as they shuffle, then touch the correct cup.
ShellGameColorLampTouch       Observe which color is under each cup, then touch the cup matching the lamp color.
ShellGameShuffleColorLampTouch  Observe which color is under each cup, track the cups as they shuffle, then touch the cup matching the lamp color.
Intercept                     Intercept the rolling ball by moving to its path and deflecting it toward the target.
InterceptGrab                 Intercept the rolling ball and grasp it to stop it.
TakeItBack                    Push the cube onto the red target, and when the target changes color, return the cube to its original position.
```

颜色集合与顺序系列（区别只在最后一句是否要求按序）：

```text
BunchOfColors / SeqOfColors   Observe which colored cubes appear during the cue, wait, then touch all of them in any order and press the center button.
ChainOfColors                 Observe which colored cubes appear during the cue, wait, then touch all of them in the same order as the cubes were shown and press the center button.
```

时序、过程、清单、前瞻等多阶段系列：

```text
BlinkCountButtonPress   Count how many times the blue lamp blinks, press the red button exactly that many times when the red lamp turns green, then press the black button to submit your answer.
TraceShape              Watch the red cube trace a shape on the table. When the lamp turns green, pick up the green cube and trace exactly the same shape.
TraceShapeSeq           Watch the red cube trace a sequence of shapes. When the lamp turns green, pick up the green cube and trace the same sequence in order. After finishing all shapes, press the button to submit your answer.
BatteriesCheckerEasy    Find all working batteries by inserting each one into the socket, observing the lamp result, and then pressing the button to confirm.
BatteriesCheckerHard    Find all working batteries by inserting each one into the socket, observing the lamp result, returning it from the socket to its initial slot, and then pressing the button to confirm.
GatherAndRecall         Move all cubes onto the disc. A lamp will briefly flash while you work. After all cubes are placed, press the button matching the flash color.
```

Rotate 与 TimedTransfer 两系列的指令是模板，逐 episode 代入具体数值。RotateLenient 用 `LANGUAGE_INSTRUCTION_TEMPLATE = "Rotate the peg by {angle_deg} degrees to match the target angle."`，把该 episode 采样的 `target_angle` 换算成角度填进去；RotateStrict 在句尾多一句 `while keeping the center of the peg in place.`。TimedTransfer 则把要数到的 `DELAY_STEPS` 直接写进指令，例如 Hard 变体是 `When the white lamp turns green, start counting steps from that exact moment. Move the blue cube from the green disc to the red disc exactly on step 200 of that count.`

## 变体与命名

同一系列的难度参数控制记忆负载：数量档（RememberColor 的 3 / 5 / 9）增加要区分的项数，速度档（Intercept 的 Slow / Medium / Fast）压缩反应时间，Easy / Medium / Hard 则加长时序或提高复杂度。Long 变体保持任务不变、把时间跨度拉长，用来考察同一记忆需求在更长 episode 上的保持。步数区间随难度和 Long 变体展开，例如 ShellGameTouch 固定 30 步，RememberColor 标准 25 步、Long 变体 600 步，BatteriesCheckerHard 从 3 电池的 1080 步到 6 电池的 2160 步。

## 采集来源与本地变体

轨迹的采集方式记在 `Data Source` 列，全 90 个环境里 34 个用 PPO oracle 采集、56 个用运动规划采集。短程原子任务大多 PPO 能稳定求解，标为 PPO；较长的多阶段任务（颜色集合、Trace、Blink、Timed、Batteries、Gather，以及各系列的 Long 变体）PPO 难以收敛，改用脚本化运动规划，标为 MP。

90 个环境是标准 benchmark 的范围。仓库里还有少量本地变体（例如 `BatteriesCheckerHard-9/12/15`，horizon 到 3240 至 4320 步），没有随附数据、也不计入这 90 个环境。

## 导航

- 返回上级：[MIKASA-Robo-VLA](../01-mikasa.md)
- 上一节：[记忆类型体系](02-memory-taxonomy.md)
- 下一节：[记忆负载机制](04-memory-load.md)
