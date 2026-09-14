# 难度与时间跨度

MIKASA-Robo-VLA 用两组正交的旋钮调节任务：难度档在任务内部加重记忆负载，horizon 分档和 Long 变体则改变时间跨度。全部环境的 episode 长度从 25 步一直到 2160 步。

## 难度档

难度档改变的是同一任务里要记住或区分的内容，不同系列用不同方式加压。

| 难度维度 | 档位 | 代表系列 | 加压方式 |
|---|---|---|---|
| 数量 | 3 / 5 / 9、3x2 / 3x3 / 5x3、3 / 5 / 7、1 / 3 / 5 / 7 / 9、3 / 6 | RememberColor、RememberShapeAndColor、BunchOfColors、GatherAndRecall、BatteriesChecker | 增加要区分或记住的项数 |
| 速度 | Slow / Medium / Fast | Intercept、InterceptGrab | 压缩观察和反应的时间 |
| 角度 | 正角 / 带符号角 | RotateLenient、RotateStrict | 扩大目标角度的取值范围 |
| 复杂度 | Easy / Medium / Hard | TraceShape、TraceShapeSeq、BlinkCountButtonPress、TimedTransfer | 加长要复现的序列、要数的计数或轨迹复杂度 |

这些档位对应源码里的具体取值：

- 数量档直接对应场上竞争的项数。RememberColor / FindImposterColor 的 `COLORS` 为 3 / 5 / 9，RememberShape 的 `SHAPES` 同为 3 / 5 / 9，RememberShapeAndColor 的网格 `3*2 / 3*3 / 5*3` 即 6 / 9 / 15 个形色组合。
- 速度档压缩反应时间。Intercept 与 InterceptGrab 的球速区间 `VELOCITY_RANGE` Slow 为 `(0.25, 0.5)`、Medium `(0.5, 0.75)`、Fast `(0.75, 1.0)`。
- 复杂度档加长时序或轨迹。BlinkCountButtonPress 的闪烁次数区间 `BLINK_COUNT_RANGE` 标准变体 Easy `[1,3]`、Medium `[1,5]`、Hard `[1,7]`，Long 变体扩到 `[1,10]` / `[10,20]` / `[20,30]`。TimedTransfer 要数到的步数 `DELAY_STEPS` 标准变体为 100 / 150 / 200，Long 变体为 300 / 500 / 1000。TraceShape 的可选形状 `AVAILABLE_SHAPES` Easy 只有圆 `[0]`、Medium 圆方 `[0,1]`、Hard 圆方三角 `[0,1,2]`；TraceShapeSeq 再叠一层序列长度，取 2 到 5。
- 电池与容量档增加要检验或记住的项。BatteriesChecker 的电池总数与其中可用数为 3/1、6/3、9/5（本地还有 12/7、15/9），插入判定容差 `SOCKET_INSERT_XY_TOL=0.010`、`SOCKET_INSERT_Z_TOL=0.025`。GatherAndRecall 的方块数 `N_CUBES` 为 1 / 3 / 5 / 7 / 9，闪光持续 `FLASH_DURATION_STEPS=[8,14]` 步。

## Horizon 分档

按 episode 长度，90 个任务分成三档。分档不是评测代码按阈值现算的，而是直接写在 `mikasa_robo_vla_envs.csv` 的 `Horizon Split` 列里，评测时读这一列、并对照 `benchmarking.py` 的 `SUPPORTED_SPLITS = ("short", "medium", "long", "all")` 校验。三档在 `Max Length` 上的跨度大致如下：

```text
Short   Max Length 约 ≤ 200
Medium  Max Length 约 201 – 601
Long    Max Length 约 > 601
```

| 分档 | 任务数 | 步数范围 | 25 Hz 下时长 | 典型记忆需求 |
|---|---|---|---|---|
| Short | 38 | 25 – 200 | 1 – 8 秒 | 快速编码线索、短期回忆 |
| Medium | 30 | 201 – 601 | 8 – 24 秒 | 中等长度上的持续工作记忆 |
| Long | 22 | 602 – 2160 | 24 – 86 秒 | 长时保持、多阶段推理、过程复现 |

## 每分档的记忆类型分布

三档的记忆类型构成不同，评测时按分档汇总 SR，因此各档的能力侧重也不一样：

```text
Short  (38): Spatial 14 · Object 9 · Negative 9 · Temporal 3 · Tracking 2 · Prospective 1
Medium (30): Object 9 · Capacity 6 · Temporal 4 · Sequential 3 · Procedural 3 · Tracking 2 · Prospective 2 · Checklist 1
Long   (22): Capacity 6 · Temporal 5 · Checklist 3 · Procedural 3 · Sequential 3 · Prospective 2
```

Short 档以空间、对象、否定这类观察一次再作答的原子任务为主；Medium、Long 档逐步转向容量、时序、清单、过程这些要在更长跨度里持续记忆或多阶段验证的任务。

## Long 变体

许多系列在标准变体之外提供一个 Long 变体：任务本身不变，只把 cue 与 memory（或追踪、计数）阶段的步数拉长，考察同一记忆需求在更长时间跨度上是否还稳。例如 RememberColor 从 25 步拉到 600 步、memory 段从几步拉到 50 至 450 步，ShellGameShuffleTouch 的交换次数从 2 至 4 提到 5 至 15，BlinkCountButtonPress 的 Long 变体统一到 1200 步。短程原子任务（如 ShellGameTouch、Intercept、FindImposter）没有 Long 变体，BatteriesCheckerHard 本身已属长时程。

逐任务的确切步数、难度档和是否有 Long 变体，记在 `mikasa_robo_vla_envs.csv` 的 `Max Length`、`Difficulty`、`Horizon Split` 列。

## 导航

- 返回上级：[MIKASA-Robo-VLA](../01-mikasa.md)
- 上一节：[记忆负载机制](04-memory-load.md)
- 下一节：[观测与动作接口](06-observation-and-action.md)
