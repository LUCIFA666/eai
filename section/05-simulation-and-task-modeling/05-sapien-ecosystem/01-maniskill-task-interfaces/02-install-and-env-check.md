# 安装与环境自检

仿真教程里，环境问题常常比代码本身更先出现。能导入 Python 包，不代表相机能渲染；能跑单个环境，不代表 GPU batch 可用。因此，ManiSkill 的自检应该分层做。

本节不要求读者一次把所有能力都跑通。一个没有 CUDA 或 headless 渲染条件的机器，仍然可以先学习 `state` 观测、Gymnasium 接口和任务成功判定。关键是知道当前环境跑到了哪一层。

## 第一层：导入检查

先确认当前 Python 环境能导入 ManiSkill 和 SAPIEN：

```bash
python -c "import mani_skill, sapien; print('mani_skill ok'); print(getattr(sapien, '__version__', 'unknown'))"
```

如果这里失败，后面的任务创建、渲染和 GPU batch 都不需要继续排查。先确认 `python` 和安装依赖时使用的 `pip` 是否来自同一个环境。

## 第二层：state 任务冒烟

第一次运行建议先跳过 GPU，只看单环境和基础渲染链路：

```bash
python labs/04-simulation/maniskill_pickcube_artifacts.py --steps 50 --skip-gpu
```

这个命令会尝试创建 `PickCube-v1`，用 `obs_mode="state"` 跑若干步，并保存 summary、space、reset 图和 rollout 视频。这里的目标不是让机器人成功抓起方块，而是确认任务接口可以创建、推进、记录。

## 第三层：视觉和批量

视觉观测需要相机和渲染链路。GPU batch 还会涉及 CUDA、PhysX 初始化和张量 device。它们应该在 state 冒烟之后单独检查。

如果机器有 CUDA 环境，可以再跑：

```bash
python labs/04-simulation/maniskill_pickcube_artifacts.py --only-vector --num-envs 16
```

仓库随附的产物已经覆盖下面几类 probe。读者在自己的机器上重跑时，也可以按这张表判断当前环境跑到了哪一层：

| 检查项 | 它说明什么 | 典型产物 |
|---|---|---|
| state smoke | 任务能创建，物理能推进，`reset()` / `step()` 可用 | `maniskill_pickcube_summary.json` |
| rgbd probe | 相机观测和渲染链路可用 | `maniskill_pickcube_rgb.png`、`maniskill_pickcube_depth.png` |
| control modes | 不同控制模式对应的 action shape 可读 | `maniskill_pickcube_summary.json` |
| vector probe | `num_envs > 1` 时 batch shape 和 device 可读 | `maniskill_pickcube_vector.json` |
| CPUGymWrapper | 批量接口可以包成传统单环境 Gym 形态 | `maniskill_pickcube_wrapper.txt` |

这些检查不等价。state 能跑，不代表 `rgbd` 一定能渲染；`rgbd` 能渲染，也不代表 GPU batch 已经可用。

## `.skipped` 怎么读

如果依赖缺失或当前机器不支持某个 probe，脚本会写出 `.skipped`。这类文件不是“教程失败”的标志，而是环境诊断结果：它告诉你当前机器暂时只能覆盖哪一部分。

| skip 类型 | 通常表示 |
|---|---|
| `maniskill_pickcube.skipped` | 基础导入或任务创建失败 |
| `maniskill_pickcube_rgbd.skipped` | 任务可跑，但视觉 / Vulkan / headless 渲染链路没有通过 |
| `maniskill_pickcube_vector.skipped` | 单环境可跑，但 GPU batch 或初始化顺序没有通过 |

读教程时可以先沿着已经通过的层继续学。比如只能跑 state，也足够学习 `reset()`、`step()`、action space、reward 和 `info["success"]`；等换到合适机器后，再补视觉和 GPU batch。

## 小结

- ManiSkill 自检要分层：导入、state、rgbd、GPU batch、wrapper。
- 第一次运行先看 state 冒烟，不要一上来就把视觉和 GPU 问题混在一起。
- `.skipped` 是环境诊断结果，它告诉你当前机器能学习到哪一层。
- 本章不要求读者在没有准备的机器上强行安装大依赖。

## 导航

- 上一页：[ManiSkill 是什么](01-what-is-maniskill.md)
- 返回上级：[ManiSkill 任务接口与 PickCube 实战](../01-maniskill-task-interfaces.md)
- 下一页：[PickCube 最小闭环](03-pickcube-minimal-loop.md)
