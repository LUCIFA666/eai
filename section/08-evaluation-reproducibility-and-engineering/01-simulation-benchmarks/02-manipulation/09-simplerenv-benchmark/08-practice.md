# 动手练习

前面七个节把 SimplerEnv 的概念、安装、架构、环境创建、单步调试、多步 rollout 和结果解读都过了一遍。这一节把余下的实操内容收尾：文件该怎么放，常见错误怎么排，然后通过三个动手练习把整条链路自己跑一遍。

## 前置概念

读这一节前，建议先通读前面七个节的完整内容，尤其是：

- [安装与版本检查](02-installation.md)：确保环境已正确安装。
- [单步调试](05-step-debug.md)：理解 `simplerenv_step_debug.py` 的作用。
- [多步 rollout 与视频](06-rollout-and-video.md)：理解 `simplerenv_rollout_video.py` 的参数。
- [结果解读与下一步](07-result-and-next.md)：知道 smoke test 和正式评测的区别。

## 本节目标

读完并完成本节后，你应该能做到：

1. 按建议的文件结构放置脚本、运行结果和文档素材。
2. 识别并修复四个常见易错问题。
3. 独立完成三个动手练习：复现单步调试、对比动作模式、换任务试运行。

## 文件放置建议

为了和本仓库已有章节保持一致，建议这样放：

```text
section/08-evaluation-reproducibility-and-engineering/01-simulation-benchmarks/
├── 09-simplerenv-benchmark.md
├── 09-simplerenv-benchmark/
│   ├── 01-what-is-simplerenv.md
│   ├── 02-installation.md
│   ├── 03-architecture.md
│   ├── 04-first-environment.md
│   ├── 05-step-debug.md
│   ├── 06-rollout-and-video.md
│   ├── 07-result-and-next.md
│   └── 08-practice.md
└── ../assets/
    ├── simplerenv-os-gpu-python.png
    ├── simplerenv-env-list.png
    ├── simplerenv-output-files.png
    ├── simplerenv-code-architecture.svg
    ├── simplerenv-rollout-flow.svg
    ├── simplerenv-step-000-reset.png
    ├── simplerenv-step-001-after-zero-action.png
    ├── simplerenv-small-random-008-frame-000.png
    ├── simplerenv-small-random-008-frame-010.png
    ├── simplerenv-rollout-zero.mp4
    ├── simplerenv-rollout-small-002.mp4
    └── simplerenv-rollout-small-008.mp4

labs/11-eval/
├── simplerenv_env_check.py
├── simplerenv_step_debug.py
└── simplerenv_rollout_video.py

runs/11-eval/
├── simplerenv_env_check.txt
├── simplerenv_env_list.txt
├── simplerenv_output_files.txt
├── simplerenv_step_debug/
├── simplerenv_rollout_video_zero/
├── simplerenv_rollout_video_small/
└── simplerenv_rollout_video_small_008/
```

文档图片和视频放 `assets/`，方便 Markdown 直接引用；可复现实验脚本放 `labs/11-eval/`；运行结果放 `runs/11-eval/`，方便和其它评测章节统一管理。图片、视频和 JSON 路径应在 Markdown 中保持相对路径，方便仓库迁移和网页渲染。后续更新实验时，只要重新运行 `labs/11-eval/` 下的脚本，再同步替换 `assets/` 中的展示文件即可。

## 常见易错点

### 1. `env.step()` 时 Segmentation fault

如果 `env.reset()` 能正常返回图像，但一执行 `env.step(action)` 就崩溃，并且 `PYTHONFAULTHANDLER=1` 显示错误位置在：

```text
ManiSkill2_real2sim/mani_skill2_real2sim/agents/controllers/pd_ee_pose.py
compute_ik
```

优先检查 NumPy 版本：

```bash
python - <<'PY'
import numpy
print(numpy.__version__)
print(numpy.__file__)
PY
```

如果输出是 `2.x`，先降回：

```bash
python -m pip uninstall -y numpy opencv-python opencv-python-headless opencv-contrib-python opencv-contrib-python-headless
python -m pip install --no-cache-dir --force-reinstall "numpy==1.24.4" "opencv-python==4.9.0.80"
```

本节的实际排错就是从 NumPy 2.2.6 降到 1.24.4 后解决的。

### 2. 只生成 PNG，没有 MP4

先确认你跑的是 `simplerenv_rollout_video.py`，不是 `simplerenv_step_debug.py`。单步调试脚本只保存两张 PNG 和一个 `result.json`，不会保存视频。

然后安装视频依赖：

```bash
python -m pip install imageio imageio-ffmpeg
```

脚本里已经做了兜底：如果 MP4 保存失败，会退回保存 GIF。

### 3. 看到 `pkg_resources is deprecated` 警告

这是 SAPIEN 依赖链里触发的 warning，不影响本节实验。如果环境能正常 `reset` 和 `step`，可以先忽略。

### 4. 小随机动作没有完成抓取

这是预期行为。小随机动作只是接口测试，不是策略。真正的策略评测需要接入 RT-1、Octo 或自己的 policy wrapper，然后让动作来自策略推理结果。

## 自查问题

1. 为什么 `env.reset()` 成功不等于 SimplerEnv 已经完整跑通？
2. `observation_keys` 里的 `image`、`agent`、`extra` 分别可能服务于哪些策略输入？
3. 本节为什么先跑零动作，而不是直接跑大随机动作？
4. `success=false` 在本节为什么不是错误？什么时候它才是正式评测中的失败结果？
5. 如果换机器后 `env.step()` 又发生 segmentation fault，你会先检查哪些版本？
6. 如果要接入自己的 VLA 策略，应该替换脚本里的哪一行？

## 动手练习

### 练习 1 `[复现]`：重新生成单步调试结果

运行：

```bash
PYTHONFAULTHANDLER=1 python -u labs/11-eval/simplerenv_step_debug.py
```

成功标准：

```text
runs/11-eval/simplerenv_step_debug/
├── step_000_reset.png
├── step_001_after_zero_action.png
└── result.json
```

并且 `result.json` 里 `terminated=false`、`truncated=false`。

### 练习 2 `[观察]`：比较零动作和 small-random 动作

分别运行：

```bash
PYTHONFAULTHANDLER=1 python -u labs/11-eval/simplerenv_rollout_video.py \
  --action-mode zero \
  --steps 10 \
  --out-dir runs/11-eval/simplerenv_rollout_video_zero
```

```bash
PYTHONFAULTHANDLER=1 python -u labs/11-eval/simplerenv_rollout_video.py \
  --action-mode small-random \
  --action-scale 0.08 \
  --steps 20 \
  --out-dir runs/11-eval/simplerenv_rollout_video_small_008
```

成功标准：

- 两个目录都生成 `rollout.mp4` 和 `result.json`。
- small-random 版本的视频里，机械臂位置比零动作版本更明显地发生变化。
- 两个结果中的 `success` 都可以是 `false`，因为没有接入策略。

### 练习 3 `[扩展]`：换一个任务试运行

把任务名换成：

```text
google_robot_open_drawer
```

运行：

```bash
PYTHONFAULTHANDLER=1 python -u labs/11-eval/simplerenv_rollout_video.py \
  --task google_robot_open_drawer \
  --steps 10 \
  --action-mode zero \
  --out-dir runs/11-eval/simplerenv_open_drawer_zero
```

观察 `instruction`、第一帧图像和 `reset_info` 是否发生变化。

## 参考资料

- SimplerEnv GitHub 仓库：https://github.com/simpler-env/SimplerEnv
- SimplerEnv 项目主页：https://simpler-env.github.io/
- 论文：Evaluating Real-World Robot Manipulation Policies in Simulation：https://arxiv.org/abs/2405.05941
- ManiSkill / SAPIEN 渲染相关排错：https://maniskill.readthedocs.io/

## 导航

- 上一节：[结果解读与下一步](07-result-and-next.md)
- 返回上级：[SimplerEnv](../09-simplerenv-benchmark.md)
- 下一节：[RLBench](../10-rlbench-benchmark.md)
