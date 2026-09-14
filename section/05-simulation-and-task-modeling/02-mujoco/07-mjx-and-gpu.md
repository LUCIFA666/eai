# MJX 与 GPU 并行

训练一个 RL 策略动辄要上亿步仿真。CPU 上多开几十个环境，很快就撞到核心数的墙；而 GPU 天生适合“几千个环境同时算同一件事”。MJX 就是 MuJoCo 官方的 GPU 后端，用 JAX 让成千上万个仿真实例并行跑在一张显卡上。

## 前置概念

读这一部分前，建议先理解：

- **mjModel / mjData**（详见 [mjModel vs mjData](02-modeling/06-mjmodel-vs-mjdata.md)）：MJX 把它们重新实现成 JAX 可用的版本。
- **step 循环**（详见 [MuJoCo 程序怎么运转](01-overview/02-mental-model.md)）：MJX 替换的就是这个循环。

JAX 相关概念（`jit` / `vmap` / 纯函数）会在下面的小节里逐个介绍，不要求提前会 JAX。

## 学习路径

| 小节 | 读完能回答 | 重点 |
|---|---|---|
| [为什么 MJX](07-mjx-and-gpu/01-why-mjx.md) | CPU 多环境为什么不够？MJX 和 Warp 各占什么生态位？ | GPU 并行动机、MJX 与 Warp 定位 |
| [最小迁移](07-mjx-and-gpu/02-minimal-migration.md) | 现有 mujoco 脚本怎么改成 mjx？ | jit / vmap 在迁移里的角色、最小例子 |
| [速度与 benchmark](07-mjx-and-gpu/03-speed-and-benchmarks.md) | MJX 到底快多少？什么任务最受益？ | CPU 多环境 vs MJX 的量级对比 |
| [局限与 Warp 简评](07-mjx-and-gpu/04-limitations-and-warp.md) | MJX 不支持什么？什么时候要回退？ | 局限清单、Warp 简介、选型建议 |

## 导航

- 上一节：[抓取实战](06-grasping-walkthrough.md)
- 返回上级：[MuJoCo](../02-mujoco.md)
- 下一节：[训练教程](08-training-recipes.md)
