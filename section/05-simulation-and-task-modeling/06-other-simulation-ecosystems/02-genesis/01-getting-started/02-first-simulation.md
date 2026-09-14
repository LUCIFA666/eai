# 第一次仿真

上一页把 Genesis 入门拆成两个动作：先跑通最小仿真，再回头解释背后的理解视角。这一页开始动手，但目标仍然很小：**只跑通一个最小刚体场景**。

不要一上来就加载复杂资产、打开高级渲染、跑并行训练或尝试软体。第一次仿真的成功标准很朴素：Python 能导入 Genesis，能初始化后端，能创建一个场景，能加入地面和一个机器人，能 `build()`，能 `step()`。

## 本节目标

本节围绕下面几个问题展开：

1. 第一次运行前要确认哪些环境信息？
2. 第一个脚本为什么要按 `init -> Scene -> add_entity -> build -> step` 的顺序写？
3. 最小仿真跑通后，应该保存哪些输出作为验收证据？
4. 初学时怎样把后端、viewer 和物理循环拆开排查？

## 最小运行前的环境三问

第一次仿真页不展开完整安装流程，只做最小确认。详细安装、配套环境变量和服务器缓存设置放在 [安装与环境检查](04-install-and-env-check.md) 里集中讲。这里先确认三件事：

```bash
python --version
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -c "import genesis as gs; print(getattr(gs, '__version__', 'unknown'))"
```

如果这三行都能跑，才进入下一步。否则先解决环境问题，不要急着写仿真脚本。

如果同一台机器上同时装过 MuJoCo、Isaac Sim、Isaac Lab 和 Genesis，尤其要确认 `python` 和 `pip` 属于同一个环境。下面命令默认在 bash / WSL / Linux shell 中运行：

```bash
which python
python -m pip -V
```

这两行比单独敲 `pip -V` 更可靠，因为它能避免“依赖装到 A 环境，脚本却用 B 环境运行”的问题。

共享服务器上的缓存、临时目录和大 wheel 下载放到 [安装与环境检查](04-install-and-env-check.md) 统一处理。第一次仿真只需要确认最小环境能导入，不需要一开始就安装 Nyx、视频编码或官方资产镜像。

## 第一个脚本的最小结构

Genesis 的最小脚本可以先写成这样：

```python
import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(show_viewer=False)
scene.add_entity(gs.morphs.Plane())
scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

for _ in range(1000):
    scene.step()
```

这段代码不是为了做任务，也不是为了训练策略。它只验证一件事：Genesis 的基本仿真循环能跑。

把它拆开看：

| 代码 | 作用 |
|---|---|
| `gs.init(backend=gs.cpu)` | 初始化 Genesis，并选择计算后端 |
| `gs.Scene(...)` | 创建一个仿真场景 |
| `scene.add_entity(...)` | 往场景里加入地面、机器人或物体 |
| `scene.build()` | 构建底层数据结构、准备计算和设备内存 |
| `scene.step()` | 推进仿真一步 |

这里最容易漏掉的是 `scene.build()`。在 Genesis 里，所有实体加完之后要先构建场景，再开始 step。可把它理解成“把 Python 层描述的场景变成底层能运行的数据结构”。

## 用配套脚本验收

不建议只靠手写片段验收第一次仿真。更稳的做法是直接运行本页对应的配套脚本。下面命令默认在仓库根目录的 bash / WSL / Linux shell 中运行：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 GENESIS_STEPS=1000 \
  python labs/06_genesis/01_first_simulation.py
```

`GENESIS_BACKEND` 和 `GENESIS_VIEWER` 可以按排错需要保留；`GENESIS_STEPS` 建议在首次仿真后清掉，避免同一终端会话后续运行 `run_all.sh` 时让所有脚本继承 `1000` 步。

运行通过后，重点看终端里 `[genesis-check] wrote ...` 指向的 summary。默认位置是 `runs/genesis_codecheck_*/summaries/01_first_simulation.json`；如果显式设置了 `GENESIS_RUN_DIR`，则在该目录的 `summaries/` 下查找。它应该至少包含这些字段：

```json
{
  "name": "01_first_simulation",
  "steps": 1000,
  "show_viewer": false,
  "build_seconds": 1.23,
  "step_seconds": 4.56,
  "steps_per_second": 219.3,
  "result": "passed"
}
```

这里的数字只是示意，不同机器会不同。真正要检查的是字段是否齐全、`result` 是否是 `passed`、`steps` 是否等于设置的步数、日志里有没有导入或构建错误。

第一次验收先不要追求速度。CPU 后端慢一点没关系，它的任务是把链路拆清楚：Python 环境能导入、Genesis 能初始化、场景能构建、物理能连续推进。

## 和官方第一个素材对齐

`01_first_simulation.py` 是配套的最小验收脚本；官方 showcase 里的 `physics_00_franka_cube` 则是一个更完整的刚体示例。两者不需要代码完全一样，但它们验证的是同一条入门链路：场景能构建，刚体机器人能和物体共同推进，结果能被记录下来。

下面是这个官方刚体示例真实跑出来的样子，可以先看一眼“第一次仿真”大致是什么效果，再回到摘要核对字段：

<figure class="doc-figure">
<p class="doc-figure-title">官方最小刚体示例：Franka 抓取方块</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_00_franka_cube.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_00_franka_cube.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方刚体示例 <code>examples/rigid/franka_cube.py</code> 的真实 headless 运行（1060×580）。Franka 在 <code>Plane</code> 上抓取并抬起方块，验证的正是本页第一次仿真的同一条入门链路：场景能构建、刚体机器人能与物体共同推进、结果能被记录。</p>
</figure>

运行目录 `runs/genesis_readme_showcase_canonical_20260608_055500/summaries/physics_00_franka_cube.json` 记录了真实输出：

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

这段摘要适合作为第一次仿真的参照，而不是替代。它证明官方刚体示例在该服务器环境里可以生成 133 帧 `1060x580` 视频和预览；配套脚本还要另外证明本地环境、后端、步数、`build_seconds`、`step_seconds` 和 `steps_per_second`。因此，`physics_00_franka_cube` 说明“官方最小刚体素材能跑通”，`01_first_simulation.json` 说明“本地最小链路也通过了”。

## 先用 CPU 和无 viewer

如果机器有 NVIDIA GPU，Genesis 可以使用 GPU 后端；本地桌面环境也可以打开 viewer。可是第一课建议先把变量降到最低：

```python
gs.init(backend=gs.cpu)
scene = gs.Scene(show_viewer=False)
```

这不是说 GPU 或 viewer 不重要，而是为了把“仿真核心链路”先验出来。第一次出错时，需要先确认是 Genesis API、资产路径、viewer 图形环境，还是 GPU / 驱动 / CUDA 版本问题。直接同时打开 GPU 和 viewer，会把这些问题叠在一起。

CPU 无界面跑通后，再一次只改一个变量。先试 GPU 后端：

```python
gs.init(backend=gs.gpu)
scene = gs.Scene(show_viewer=False)
```

再试 viewer：

```python
gs.init(backend=gs.cpu)
scene = gs.Scene(show_viewer=True)
```

如果 viewer 打不开，不要急着判断“Genesis 不能用”。退回 `show_viewer=False`，只验证物理循环：

```python
for _ in range(1000):
    scene.step()
```

能无界面跑通，说明仿真核心路径至少是通的；viewer、相机和离屏渲染可以在观察与渲染页单独处理。

## 第一次仿真的验收标准

建议把第一次实验验收写得具体一些：

| 验收项 | 通过标准 |
|---|---|
| 环境导入 | `import genesis as gs` 不报错 |
| PyTorch 状态 | 能打印 `torch.__version__` 和 `torch.cuda.is_available()` |
| 最小场景 | `Plane + Franka` 能完成 `scene.build()` |
| 物理循环 | 能连续 `scene.step()` 1000 次 |
| viewer 可选 | 有桌面图形环境时能看到窗口；远程或无显示环境可先关闭 viewer |
| 运行证据 | `runs/genesis_codecheck_*/summaries/01_first_simulation.json` 记录步数、耗时和通过状态 |

如果要保存证据，可以把 Python 版本、Torch 版本、是否有 CUDA、后端、步数和运行时间写进一个 JSON 文件。它不需要复杂，但能帮助以后排查“同一段代码为什么换机器不一样”。

## 常见问题

| 问题 | 优先检查 |
|---|---|
| `import genesis` 失败 | 是否装在当前 Python 环境，`pip` 和 `python` 是否属于同一个环境 |
| `torch.cuda.is_available()` 是 `False` | PyTorch CUDA wheel、显卡驱动、服务器是否暴露 GPU |
| `scene.build()` 很慢 | 首次构建可能需要准备底层结构或编译；先确认不是卡死 |
| viewer 打不开 | 先关掉 `show_viewer`，确认无界面物理循环能跑 |
| 资产找不到 | 先用官方示例资产路径，不要第一步就换自定义机器人 |

排错时保持一个原则：**一次只改一个变量**。先确认环境，再确认最小场景，再确认可视化，最后再改后端和资产。

## 读完应能回答

1. 如果 `scene.build()` 成功但 viewer 打不开，为什么还不能说 Genesis 仿真失败？
2. `01_first_simulation.json` 至少应该记录哪些字段，才能证明本地最小链路真的跑过？
3. `physics_00_franka_cube` 能证明官方刚体示例可复现，但为什么还不能替代本地的 `01_first_simulation.py`？
4. 如果第一次运行很慢，应先检查环境、资产、viewer，还是直接换 GPU 后端？为什么？

## 小结

- Genesis 第一次上手不要追求复杂任务，只跑通 `init -> Scene -> add_entity -> build -> step`。
- 安装和缓存细节集中放在环境检查页；本页只做最小导入确认。
- 第一次建议用 CPU 后端、关闭 viewer、使用最小资产，降低排错难度。
- 能连续 step 1000 次，就是进入下一页几个理解视角的起点。

## 参考资料

- Genesis World Documentation, Installation. https://genesis-world.readthedocs.io/en/latest/user_guide/overview/installation.html
- Genesis World Documentation, Hello, Genesis World. https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/hello_genesis.html

## 导航

- 上一页：[Genesis 是什么](01-what-is-genesis.md)
- 返回目录：[认识 Genesis](../01-getting-started.md)
- 下一页：[三个理解视角](03-three-mental-models.md)
