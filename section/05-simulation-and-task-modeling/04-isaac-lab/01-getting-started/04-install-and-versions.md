# 安装与版本对照

这一页偏参考。前面三页先讲“它是什么、怎么跑、怎么理解”，这一页把真正上手时最容易卡住的安装和版本问题集中放在一起。你不需要一次记住所有细节；遇到报错时回来查即可。

## 本节目标

本节围绕下面几个问题展开：

1. 安装前要先确认哪些系统、驱动、Python 和包版本？
2. 为什么不能只记一条 pip 命令？
3. 不同安装方式分别适合什么场景？
4. 安装失败时应该按什么顺序排查？

## 课程版本锁定

本节示例锁定在 **Isaac Sim 5.1.0 + Isaac Lab 2.3.2 + Python 3.11**。这一套版本组合用于保证后续 CartPole、Franka Reach、Mimic 和多 GPU 示例的命令形态一致。

官方文档会继续向前演进。若你使用 Isaac Lab 3.0 beta / Isaac Sim 6.0 / Python 3.12 这条新版路线，需要按官方版本矩阵替换 Python 版本、Isaac Sim 安装包和可能变化的命令参数。不要把新版 quickstart 与本课程 2.3.2 示例交叉混用；一旦遇到扩展找不到、任务注册失败或 checkpoint 无法加载，先核对这三项版本是否同轴。

## 先理解依赖链

Isaac Lab 不是独立仿真器，因此它的安装不能只看 Python 包。你需要同时对齐下面几层：

| 层级 | 作用 | 常见问题 |
|---|---|---|
| NVIDIA Driver | 支持 GPU 运行 Isaac Sim / PhysX / RTX | 驱动太旧导致启动失败 |
| Isaac Sim | 底层仿真、渲染和 USD 场景系统 | 版本与 Isaac Lab 不匹配 |
| Python / Conda | 课程和训练脚本运行环境 | Python 版本不对、包冲突 |
| Isaac Lab | 任务框架、训练脚本、扩展和 wrapper | 没用安装脚本导致扩展没注册 |
| RL 库 | RSL-RL、SKRL、RL-Games、SB3 等 | wrapper 或配置没对上 |

课程采用的安装思路是：**先 Isaac Sim，再 Isaac Lab**。具体版本号如果随官方升级调整，应以本仓库 `environment.yml`、课程说明和官方 quickstart 为准。

## 推荐安装顺序

下面是最小思路，不是替代官方文档的完整安装手册：

```bash
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab

conda create -n isaaclab python=3.11 -y
conda activate isaaclab

# 1) 先安装 Isaac Sim，版本按课程或官方 quickstart 对齐
pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com

# 2) 再安装 Isaac Lab 扩展
./isaaclab.sh --install
```

注意：上面的 `isaacsim==5.1.0` 是课程示例中的锁定写法。你实际安装时，应先看官方 quickstart 的版本矩阵；如果课程环境文件已经锁定版本，以课程环境为准。

## 不要裸 `pip install -e .`

初学者常犯的错是进入 Isaac Lab 仓库后直接：

```bash
pip install -e .
```

这通常不够，因为 Isaac Lab 不只是一个普通 Python 包。它包含多个扩展、任务、训练库 wrapper 和与 Isaac Sim 的连接逻辑。正确做法是使用仓库提供的安装脚本：

```bash
./isaaclab.sh --install
```

## 安装后做三个最小验收测试

安装完先不要急着写任务，先做三个最小验证。

### 1. Python 能否启动

```bash
./isaaclab.sh -p --version
```

如果这里失败，先查 conda 环境、Python 路径和 Isaac Lab 安装。

### 2. 任务是否能被识别

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
    --task=Isaac-Cartpole-v0 --headless
```

如果提示找不到任务，通常是 Isaac Lab 任务扩展没装好，或没有通过 `isaaclab.sh -p` 进入正确环境。

### 3. GUI / 渲染是否正常

训练首跑可以 headless，但之后最好用少量环境回放一次：

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
    --task=Isaac-Cartpole-v0 --num_envs=16
```

如果 headless 能跑、GUI 不能跑，问题多半在驱动、显示、远程桌面或渲染环境，而不是任务代码本身。

## 常见安装坑

| 坑 | 表现 | 正确处理 |
|---|---|---|
| 先装 Lab 后装 Sim | 找不到 Isaac Sim 模块或扩展 | 先 Isaac Sim，再 `isaaclab.sh --install` |
| 裸 `pip install -e .` | 任务、扩展或 wrapper 注册不完整 | 使用官方安装脚本 |
| Python 版本不对 | 依赖解析失败或运行时报错 | 使用课程推荐的 Python 3.11 环境 |
| 驱动太旧 | Isaac Sim 启动失败、渲染报错 | 对照官方版本表升级 NVIDIA Driver |
| conda 环境混乱 | 命令看似成功但运行找不到包 | 确认 `conda activate isaaclab` 后再安装 |
| 远程桌面 / 无显示 | GUI 回放失败但 headless 可跑 | 先用 `--headless` 验证训练，再处理显示 |
| 显存不够 | OOM 或进程退出 | 降低 `--num_envs`，关闭 GUI，减小传感器负担 |
| 已有同名环境 | `conda create -n isaaclab` 提示环境已存在 | 用 `conda create -p /path/to/conda_env python=3.11 -y` 做隔离验证 |
| GitHub 连接不稳 | `git clone` 或 checkout 在 TLS / 443 超时 | 用本地镜像、已有仓库的 `git clone --shared`，或换稳定网络后重试 |

## 版本对应怎么看

不要孤立地问“Isaac Lab 最新版是多少”。更有用的问题是：**这一套课程、Isaac Sim、Isaac Lab、Python、驱动是不是彼此匹配**。

建议记录一张环境卡片：

| 项 | 记录 |
|---|---|
| OS | 操作系统版本 |
| GPU | 型号与显存 |
| NVIDIA Driver | 版本号 |
| Python | 版本号 |
| Isaac Sim | 安装方式与版本 |
| Isaac Lab | git commit 或 release |
| 首跑任务 | `Isaac-Cartpole-v0` 是否通过 |

后面你遇到训练慢、渲染失败、任务找不到、传感器输出异常时，这张卡片比一句“环境不行”有用得多。

## 小结

- 安装顺序优先记：先 Isaac Sim，再 Isaac Lab。
- 使用 `./isaaclab.sh --install`，不要把 Isaac Lab 当普通包裸装。
- 安装后先跑三个最小验收测试：Python、CartPole 训练、少量环境回放。
- 版本问题要整套看：驱动、Isaac Sim、Isaac Lab、Python 和训练库都要匹配。

## 参考资料

- Isaac Lab Quickstart. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab GitHub. https://github.com/isaac-sim/IsaacLab
- Isaac Sim Documentation. https://docs.isaacsim.omniverse.nvidia.com/

## 安装验收与排错案例

安装完成后，至少保留下面三类验收信息，方便之后排查训练、渲染和任务注册问题：

| 验收项 | 预期现象 | 排错提示 |
|---|---|---|
| 仓库版本 | 能记录 Isaac Lab release 或 git commit | 课程示例按 2.3.2 编写；若使用新版，先确认脚本路径和参数是否变化 |
| Python 环境 | `python --version` 显示 Python 3.11.x | 若已有同名 conda 环境，优先用 `conda create -p <env_dir> python=3.11 -y` 做隔离环境 |
| GitHub 拉取 | `git clone` 后能正常 checkout | 网络不稳、TLS / 443 超时或缺 blob 时，可换稳定网络、使用本地镜像，或从已有仓库做 shared clone |

这类验收记录不需要逐条写进课程正文。正文只保留可复用的判断方法：标准主路径仍是 `git clone + conda create + ./isaaclab.sh --install`；当网络或环境冲突出现时，用隔离前缀环境和本地镜像降低污染现有环境的风险。

## 导航

- 上一页：[三个理解视角](03-three-mental-models.md)
- 返回目录：[认识 Isaac Lab](../01-getting-started.md)
- 下一页：[任务结构与 Manager 系统](../02-reading-a-task.md)
