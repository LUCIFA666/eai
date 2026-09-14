# 安装与版本对照

本页是“认识 Isaac Sim”这一部分的收尾，接着上一页。它写给准备把 Isaac Sim 装起来、或正在排查环境报错的读者。不要求你已经装好；读完后应该能判断该用哪种装法、各版本要配什么、报错先查哪一环。

## 本节目标

本节围绕下面几个问题展开：

1. 安装前要先确认哪些系统、驱动、Python 和包版本？
2. 为什么不能只记一条 pip 命令？
3. 不同安装方式分别适合什么场景？
4. 安装失败时应该按什么顺序排查？

## pip 安装流程

如果你的机器是 **Ubuntu 22.04 / 24.04 + GLIBC 2.35+ + NVIDIA 驱动正常**，推荐先走下面这条 pip 路线。课程示例锁定 **Isaac Sim 5.1.0 + Python 3.11**。

先做一次环境体检：

```bash
cat /etc/os-release
ldd --version | head -n 1
nvidia-smi
df -h .
```

如果系统是 Ubuntu 22.04 / 24.04，`ldd` 显示 `2.35` 或更高，`nvidia-smi` 能正常看到 GPU，就可以继续：

```bash
conda create -n isaacsim51 python=3.11 -y
conda activate isaacsim51

python --version
python -m pip install --upgrade pip setuptools wheel

# 补常见图形依赖；没有 sudo 权限时，这一步比 apt 更容易执行
conda install -c conda-forge libglu -y

# 不要直接用 pip，避免误用 ~/.local 里的其它 Python 版本
PYTHONNOUSERSITE=1 python -m pip install --no-cache-dir \
  "isaacsim[all,extscache]==5.1.0" \
  --extra-index-url https://pypi.nvidia.com
```

安装完成后，先验证 import，再跑一个最小 headless 仿真：

```bash
conda activate isaacsim51

PYTHONNOUSERSITE=1 python - <<'PY'
import importlib.metadata as md
print("isaacsim", md.version("isaacsim"))
from isaacsim import SimulationApp
print("SimulationApp import OK")
PY

PYTHONNOUSERSITE=1 python -m isaacsim --generate-vscode-settings
```

新建一个 smoke test：

```bash
cat > /tmp/isaacsim_smoke.py <<'PY'
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

from isaacsim.core.api import World

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()
world.reset()

for _ in range(10):
    world.step(render=False)

print("ISAAC_SIM_SMOKE_OK")
simulation_app.close()
PY

PYTHONNOUSERSITE=1 python /tmp/isaacsim_smoke.py
```

终端看到 `SimulationApp import OK` 和 `ISAAC_SIM_SMOKE_OK`，说明 Isaac Sim 的 Python 包、运行时启动、headless 物理步进这三件事都通了。后面课程里的脚本就可以在这个环境里继续跑。

这里有两个细节很重要：

- 用 `python -m pip`，不要直接用 `pip`。有些服务器的 `pip` 会指到 `~/.local` 里的旧 Python，例如 Python 3.10，导致包装错环境。
- 加 `PYTHONNOUSERSITE=1`，是为了临时屏蔽用户目录下的 Python 包，避免旧环境污染当前 conda 环境。

## 三种装法

| 装法 | 怎么装 | 适合谁 |
|---|---|---|
| **pip 包**（Isaac Sim 4.0 起）| `python -m pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com`（需 Python 3.11、Linux GLIBC 2.35+）| 想在已有 conda / venv 里用、跑脚本、配 Isaac Lab（**最推荐**）|
| **预编译包 / 工作站版** | 从 NVIDIA 下载 Isaac Sim 安装包，自带 Python 运行时（`python.sh`）| GLIBC 不够（如 Ubuntu 20.04）、要 GUI 交互、不想碰 pip |
| **容器 / 源码构建** | Docker 镜像，或 `build.sh` 从源码编译 | 集群批量、CI、需要改 Isaac Sim 源码 |

三种装法跑出来的仿真是一回事，区别只在“Python 运行时从哪来”：pip 用你自己的 Python 3.11；预编译包用它自带的；容器把整套封进镜像。本单元的脚本三种都能跑。

## 项目依赖放在 Isaac Sim 之后装

Isaac Sim 本体跑通后，再安装课程或项目自己的依赖。这样排错时能分清是 Isaac Sim 没装好，还是项目依赖引入了额外冲突：

```bash
conda activate isaacsim51
PYTHONNOUSERSITE=1 python -m pip install -r requirements.txt
```

如果项目还要接 OpenPI / LabUtopia 一类客户端，再在同一个环境里安装对应包：

```bash
PYTHONNOUSERSITE=1 python -m pip install openpi-client
```

如果你有 sudo 权限，也可以补系统级图形依赖：

```bash
sudo apt-get install libglu1-mesa libxcursor1 libxinerama1 libxi6
```

没有 sudo 权限时，前面的 `conda install -c conda-forge libglu -y` 通常已经能解决最常见的 `GLU` 缺失问题。

## 版本对应

装 Isaac Sim 不是单点安装，而是一条从“系统”到“框架”的链——任何一环不匹配都会卡住：

<figure class="doc-figure">
<p class="doc-figure-title">Isaac Sim 的版本依赖链（从下往上对齐）</p>
<div class="figure-flow">
<div class="figure-node">系统：Ubuntu 22.04 / 24.04 + GLIBC 2.35+ + NVIDIA 驱动 / CUDA</div>
<div class="figure-node">Python：课程锁定 3.11；旧版 Isaac Sim 4.x 通常配 3.10</div>
<div class="figure-node">Isaac Sim：课程锁定 5.1.0</div>
<div class="figure-node">Isaac Lab（如果用）：版本要和 Isaac Sim 对得上（见下表）</div>
</div>
<p class="doc-figure-subtitle">排查环境问题时，从最下面一环往上查：先系统，再 Python，再 Isaac Sim，最后 Isaac Lab。</p>
</figure>

几条硬性对应：

- **课程锁定 Isaac Sim 5.1.0 → Python 3.11**；旧版 **Isaac Sim 4.x → Python 3.10**。虚拟环境的 Python 版本必须和 Isaac Sim 匹配，错了 pip 直接装不上。
- **Linux pip 安装需 GLIBC 2.35+**（用 `ldd --version` 查）。Ubuntu 22.04 / 24.04 满足；Ubuntu 20.04 只有 2.31 → 改用预编译包。
- Isaac Sim 5.0 起**不再支持 Ubuntu 20.04**，官方支持 22.04 / 24.04。

Isaac Lab 和 Isaac Sim 的官方对应关系（用 Isaac Lab 才需要看）：

| Isaac Lab 版本 | 兼容的 Isaac Sim |
|---|---|
| `v2.3.x`（课程锁定 `v2.3.2`） | 4.5 / 5.0 / 5.1（课程按 5.1.0 演示） |
| `v2.2.x` | 4.5 / 5.0 |
| `v2.0.x` – `v2.1.x` | 4.5 |

## import 名称

Isaac Sim 在 **4.5 版前后做了一次扩展重命名**：老的 `omni.isaac.*` 命名空间整体迁到了 `isaacsim.*`。这意味着**同一段代码，在新旧版本里 import 路径不一样**——这是初学者复制旧教程时最常见的报错来源。

| 旧（Isaac Sim ≤ 4.x）| 新（课程锁定 Isaac Sim 5.1.0）|
|---|---|
| `from omni.isaac.kit import SimulationApp` | `from isaacsim import SimulationApp` |
| `from omni.isaac.core import World` | `from isaacsim.core.api import World` |
| `from omni.isaac.core.objects import DynamicCuboid` | `from isaacsim.core.api.objects import DynamicCuboid` |
| `from omni.isaac.sensor import Camera` | `from isaacsim.sensors.camera import Camera` |
| `omni.isaac.core.utils.*` | `isaacsim.core.utils.*` |

本单元示例脚本已统一为 `isaacsim.*`（5.1）。网上大量旧教程仍写 `omni.isaac.*`——照抄会 `ModuleNotFoundError`；按上表把 import 换成右列即可，物理逻辑、调用顺序完全一样。[上一页](02-first-simulation.md) 那段自由落体脚本也使用这套 `isaacsim.*` 写法。

## 排查顺序

报错别瞎试，照着依赖链从下往上对：

| 症状 | 多半是哪一环 | 怎么办 |
|---|---|---|
| pip 找不到包 / 装不上 | GLIBC < 2.35，或 Python 不是要求的版本 | `ldd --version`、`python --version`；不行改用预编译包 |
| 启动时报缺少 `GLU` / 图形库 | 系统图形依赖不全 | `sudo apt-get install libglu1-mesa libxcursor1 libxinerama1 libxi6`，或先 `conda install -c conda-forge libglu` |
| `import omni.isaac.*` 报 `ModuleNotFoundError` | 装的是课程锁定的 5.1.0（已改 `isaacsim.*`）| 按上面的对照表换命名空间 |
| `SimulationApp` 在第一行还是崩 | 顺序对了，但驱动 / CUDA 不匹配 | 查 NVIDIA 驱动、CUDA、Isaac Sim 版本和官方支持矩阵 |
| 远程 / 无显示器起不来 | 用了 `headless=False` | 改 `headless=True`（见 [第一次仿真：运行与验证](02-first-simulation.md)）|
| 启动几十秒像卡死 | 首次在编译 shader / 拉资源 | 正常现象，等它跑完 |

## 小结

- 三种装法选一种：日常用 **pip 包**，环境太老用**预编译包**，集群用**容器**；跑出来的仿真一致。
- 版本是一条链：**系统（GLIBC / 驱动）→ Python（5.x 配 3.11）→ Isaac Sim → Isaac Lab**，逐环对齐，排查从下往上。
- 最常见的坑是命名空间：旧版 `omni.isaac.*`、新版（4.5/5.x）`isaacsim.*`，逻辑不变、只换 import。

至此“认识 Isaac Sim”这一部分完结：你已经知道 Isaac Sim 是什么、亲手跑通了第一个仿真、用三个理解视角理解了它、也清楚了怎么装和对版本。下一部分开始正式搭世界。

## 参考资料

- NVIDIA Isaac Sim Documentation, Python Environment Installation. https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_python.html
- Isaac Lab Documentation, Installation using Isaac Sim Pip Package. https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/pip_installation.html
- Isaac Lab, Isaac Sim Version Dependency（README）. https://github.com/isaac-sim/IsaacLab

## 导航

- 返回目录：[一、认识 Isaac Sim](../01-getting-started.md)
- 上一页：[三个理解视角](03-three-mental-models.md)
- 下一页：[二、场景构建与坐标约定](../02-building-a-world.md)
