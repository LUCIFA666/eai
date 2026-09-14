# 训练与评测

前两部分完成了 scene 搭建、任务逻辑定义。最后一步是把任务交给学习算法，让策略在并行环境里反复采样、更新、保存 checkpoint，并回放验证。

本部分聚焦训练启动、回放评测和训练过程调试。训练不是最后的黑盒按钮，它会把前面所有设计选择放大：观测缺目标，策略不知道往哪走；动作尺度过大，曲线震荡；奖励被钻空子，视频行为会异常；随机化过强，初期可能完全不收敛。策略导出、Sim2Real 和真机部署留给后续专门部分。

## 本节目标

本节围绕下面几个问题展开：

1. 一次 Isaac Lab 训练从任务 ID 到 checkpoint 会经过哪些环节？
2. train、play、日志、视频和 TensorBoard 曲线分别应该怎么看？
3. 配置系统、训练库、随机化和分布式训练之间是什么关系？
4. reward 不涨、吞吐低或显存爆掉时，应该按什么顺序排查？

## 学习路径

### 训练方法

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [启动训练并读懂训练曲线](05-training/01-train-and-read-curves.md) | 怎么启动训练？日志和曲线说明策略学到了什么？ | train / play、checkpoint、TensorBoard、reward、episode length |
| [配置系统与 CLI](05-training/02-config-and-cli.md) | 不改代码如何改任务和算法参数？ | `@configclass`、Hydra 覆盖、入口点、wrapper、续训 |
| [训练库对接](05-training/03-rl-libraries.md) | RSL-RL、RL-Games、SKRL、SB3 如何启动、记录和回放？ | train / play、wrapper、checkpoint、TensorBoard |
| [模仿学习与官方示例](05-training/04-imitation-learning.md) | 不写奖励时，如何用示教数据训练策略？ | teleop、Recorder、HDF5、Mimic、robomimic |

### 优化与扩展

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [域随机化](05-training/05-domain-randomization.md) | 如何避免策略只适应一种仿真参数？ | Event System、物理随机化、观测噪声、视觉随机化 |
| [多 GPU 与分布式](05-training/06-distributed.md) | 单卡不够时如何扩展训练？ | `torchrun`、每卡环境数、学习率缩放、PBT |
| [性能优化与调试](05-training/07-performance-debug.md) | reward 不涨、吞吐低、显存爆，先查什么？ | 排障顺序、`num_envs`、传感器频率、录像、markers |

## 训练流水线

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-training-pipeline.svg" alt="Isaac Lab 训练流水线" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">Isaac Lab 训练流水线：并行环境经 VecEnv wrapper 接到 RL 库，训练过程产生日志、视频和 checkpoint。</figcaption>
</figure>

可以把训练理解成一条链：

```text
task id
  -> gym.register 找到 env_cfg 和 agent_cfg
  -> gym.make 创建 Isaac Lab 并行环境
  -> VecEnv wrapper 适配 RL 库接口
  -> runner / trainer 采样和更新策略
  -> logs / checkpoints / videos
  -> play.py 回放评测
```

## 读完本部分后

完成这一部分后，应该能启动一次训练、找到日志和 checkpoint、用 `play.py` 回放策略、切换常见 RL 库入口，并在 reward 不涨、吞吐低或显存爆掉时按任务闭环、训练配置、系统性能的顺序排查。

## 导航

- 上一页：[任务逻辑配置](04-task-logic.md)
- 返回上级：[Isaac Lab](../04-isaac-lab.md)
