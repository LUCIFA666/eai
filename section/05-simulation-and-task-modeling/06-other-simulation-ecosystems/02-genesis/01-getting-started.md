# 认识 Genesis

Genesis 不是新版 MuJoCo，也不是轻量版 Isaac Sim，而是一个 Python-first 的多物理仿真平台。接下来不要急着碰软体、流体和训练库，先把最小刚体场景跑通，再解释脚本背后的结构。

这一组的任务不是把 Genesis 所有功能介绍完，而是让读者先形成一个稳定的入口：Genesis 到底是什么，最小脚本怎么跑，场景什么时候构建，物理循环什么时候推进，最后再集中处理安装和环境检查。只要这个入口没有打稳，后面所有控制、观测、并行和多物理都会变成“看起来像能跑，其实不知道哪里出了问题”。

## 本节目标

本节围绕下面几个问题展开：

1. Genesis 是什么，为什么不能只理解成另一个物理引擎？
2. 一个最小 Genesis 脚本为什么要按 `init -> Scene -> add_entity -> build -> step` 展开？
3. `Scene / Entity / 多物理 / n_envs` 这些概念分别解决什么问题？
4. 安装、版本、后端和 viewer 问题为什么放在本组后半段集中处理？
5. 跑通第一个脚本后，应该留下哪些证据，而不是只说“能跑”？

## 为什么先讲“认识”

Genesis 的第一印象很容易被几个词带偏：多物理、GPU、并行、生成式仿真、Physical AI。它们都重要，但不适合作为第一步。初学者真正会卡住的地方通常更基础：

| 学习者的问题 | 如果不先处理会怎样 |
|---|---|
| 当前使用的是哪个 Python？ | `pip install` 成功，但运行脚本时仍然 `ModuleNotFoundError` |
| Torch 装的是 CPU 版还是 CUDA 版？ | 以为是 Genesis 问题，其实是 PyTorch 和驱动没对上 |
| viewer 打不开是不是仿真失败？ | 把图形窗口问题误判成物理引擎不能用 |
| `scene.build()` 为什么必须在 `step()` 前？ | 不知道 Python 层场景描述和底层运行数据结构的区别 |
| 第一次运行慢是不是卡死？ | 忽略首次构建、编译或资源准备带来的等待 |

所以“认识 Genesis”不是一句介绍，而是一套入门顺序：先把环境、后端、场景构建和无界面运行拆开。它比直接看一个复杂 demo 更慢一点，但更适合打基础。

## 第一轮只验证刚体链路

Genesis 能处理更宽的物理对象，但第一轮只用刚体。推荐最小对象是 `Plane + Franka`：

```text
Python 环境
  -> import genesis as gs
  -> gs.init(backend=...)
  -> Scene(show_viewer=...)
  -> Plane + Franka
  -> scene.build()
  -> scene.step()
```

这条链路有两个好处。第一，它和后面机器人控制直接相连；第二，它不依赖复杂资产、传感器、软体参数或训练框架。出错时能比较快定位到环境、资产路径、viewer 或后端。

如果这一步还没跑通，不建议继续看并行环境或多物理。否则后面报错时，很难判断是 Genesis 基础链路有问题，还是新增功能本身有问题。

## 配套脚本怎么用

这一组对应两个脚本：

```bash
python labs/06_genesis/00_env_check.py
python labs/06_genesis/01_first_simulation.py
```

第一次入门验收先单独运行这两个脚本。下面命令默认在仓库根目录的 bash / WSL / Linux shell 中运行。`run_all.sh` 是 `00` 到 `05` 的全量 codecheck，会继续运行多刚体、机器人控制、相机和并行环境脚本，不适合作为“第一次仿真”唯一入口：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 python labs/06_genesis/00_env_check.py
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 GENESIS_STEPS=1000 python labs/06_genesis/01_first_simulation.py
```

第一次建议固定三个选择：

| 设置 | 建议 | 原因 |
|---|---|---|
| `GENESIS_BACKEND` | `cpu` | 先排除 CUDA、驱动和显存变量 |
| `GENESIS_VIEWER` | `0` | 先验证无界面物理循环 |
| `GENESIS_STEPS` | `1000` | 足够确认连续 step，不至于耗时太久 |

这不是说 CPU 或无界面才是最终配置，而是第一轮排错应该尽量少变量。等 `01_first_simulation.py` 通过后，再打开 viewer 或切换 GPU。

需要一次性复核本组到并行环境的所有配套脚本时，再运行：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 bash labs/06_genesis/run_all.sh
```

## 读日志时看什么

运行后先看 `runs/genesis_codecheck_*/summaries/`，不要先盯着窗口。入门阶段最有价值的是这些字段：

| 字段 | 说明 |
|---|---|
| `python_executable` | 当前到底用哪个 Python 运行 |
| `torch_version` | PyTorch 版本 |
| `torch_cuda_available` | 当前环境是否能看到 CUDA |
| `genesis_version` | Genesis 包版本 |
| `genesis_backend_env` | 当前脚本请求的 Genesis 后端 |
| `steps` | 脚本实际推进了多少步 |
| `build_seconds` | 场景构建耗时 |
| `step_seconds` | step 循环耗时 |
| `result` | 脚本是否完成预期验收 |

这些字段能帮助形成工程习惯：问题不是“这台电脑能不能跑 Genesis”，而是“当前 Python、当前包版本、当前后端、当前脚本参数下，哪一步失败”。

官方 showcase 运行目录中，`physics_00_franka_cube` 摘要是一个可以直接引用的例子。它不是一句“通过了”，而是把示例路径、分辨率、帧数、耗时和错误字段都写清楚：

```json
{
  "id": "physics_00_franka_cube",
  "example": "examples/rigid/franka_cube.py",
  "resolution": [1060, 580],
  "duration_seconds": 10.321840991266072,
  "captured_frames": 133,
  "capture_errors": [],
  "error": null,
  "result": "passed"
}
```

对应日志里还能看到更多环境信息。比如这份固定运行快照实际使用 `genesis-world==1.0.0`，后端是 `gs.cuda`，设备是 `NVIDIA GeForce RTX 4090`。如果按当前未 pin 版本重新安装，可能会得到更新的 `genesis-world` 版本，warning 或细节输出不一定逐字相同。日志同时保留了 warning，例如 PyTorch 版本提示、MJCF tendon 近似、初始位姿超过关节限位、求解器 time constant 被调整等。入门时不要把所有 warning 都当成失败；先看 `result`、`error` 和产物是否齐全，再判断 warning 是否影响本节目标。

## 学习顺序

这一组围绕同一条最小链路展开，每一步都要落到可验证结果：

| 页面 | 重点 |
|---|---|
| [Genesis 是什么](01-getting-started/01-what-is-genesis.md) | 平台定位和四层结构 |
| [第一次仿真](01-getting-started/02-first-simulation.md) | 最小场景、无界面 step 验收 |
| [三个理解视角](01-getting-started/03-three-mental-models.md) | 用 `Scene / Entity`、多物理和批量环境解释已跑通的脚本 |
| [安装与环境检查](01-getting-started/04-install-and-env-check.md) | Python、PyTorch、后端、viewer 和配套检查脚本 |

这一组读完后，读者应该能回答一个很朴素的问题：Genesis 脚本到底是在什么时候描述世界，什么时候构建世界，什么时候推进世界。

## 通过标准

这一组读完后，不要求读者会做任务，也不要求理解软体或流体。通过标准只有四条：

1. 能说清楚 `gs.init()`、`Scene`、`add_entity()`、`build()`、`step()` 的顺序。
2. 能用 `GENESIS_VIEWER=0` 跑通最小刚体场景。
3. 能在 JSON 摘要里找到 Python、Torch、Genesis 和后端信息。
4. 能解释 viewer 失败为什么不等于仿真失败。

如果这四条都成立，再进入“场景、机器人与观测”才自然。下一组会把最小世界变成机器人链路：先控制，再观察。

## 小结

- Genesis 入门先验证无界面脚本链路，再讨论 viewer、渲染和高级功能。
- `physics_00_franka_cube` 的价值不只是画面，而是它留下了帧数、耗时、错误字段和日志。
- 第一组的验收重点是环境、最小场景、理解视角和可复查摘要。
- 读者能解释 `init -> Scene -> add_entity -> build -> step`，才适合继续读机器人控制。

## 导航

- 上一页：[Genesis](../02-genesis.md)
- 返回目录：[Genesis](../02-genesis.md)
- 下一页：[Genesis 是什么](01-getting-started/01-what-is-genesis.md)
