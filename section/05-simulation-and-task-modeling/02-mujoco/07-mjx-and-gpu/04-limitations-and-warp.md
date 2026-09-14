# 局限与 Warp 简评

MJX 不是 MuJoCo 的"完整快速版"，它是 MuJoCo 的一个子集，用 JAX 重新实现。一些原生支持的特性 MJX 还没补齐，遇到这些时往往要么回 CPU，要么用 Warp。这一页把已知局限列清。

## 本节目标

本节回答几个问题：

1. MJX 目前还不支持哪些特性？
2. 它的数值结果和原生 MuJoCo 有什么差异？
3. MuJoCo Warp 是什么？
4. 什么场景该选 MJX、Warp 还是原生？

## MJX 当前不支持的特性

MJX 是 MuJoCo 的一个子集，但特性支持随版本快速扩展，早期不支持的 `tendon`、`equality` 约束如今都已补上。截至写作时，主要的已知局限大致如下（以官方 MJX 文档为准）：

| 不支持 / 受限的特性 | 影响 | 替代方案 |
|---|---|---|
| Flex / 可变形体 | 软体、布料、绳索类仿真不能用 | 回 CPU |
| 部分 contact sensor 语义 | 按 site / body / subtree 匹配、netforce 归并的接触传感器不支持 | 换用支持的 sensor 形式，或把状态传回 CPU 读 |
| 部分碰撞几何对 | 个别 geom **配对**（如 `cylinder`×`box`、`cylinder`×`mesh`）尚未实现；`cylinder`×`plane` 可用 | 换用支持的配对，或回 CPU |
| 部分 solver / 积分器选项 | 某些 cone、jacobian、integrator 组合不支持（如 elliptic cone 配 condim=1） | 换成支持的组合 |
| 引擎插件（plugins） | 自定义引擎插件不支持 | 回 CPU |

渲染方面，MJX 没有内置渲染器，需要把状态传回 CPU 用原生 `Renderer`；面向批量的渲染支持目前主要在 MuJoCo Warp 一侧（见下文简介），截至写作时 JAX 版的 MJX 仍以传回 CPU 渲染为主。

还有一点关于性能和显存：带完整碰撞网格的复杂场景（比如整套 Panda）在 MJX 上首次 JIT 编译较慢、显存占用也高，小显存的卡上做大批量容易 OOM。menagerie 为不少机器人提供了 mjx 简化碰撞变体（文件名形如 `*_mjx.xml`，少数如 Panda 为 `mjx_*.xml`），正是为大批量 MJX 训练准备的。上大批量之前，先用单环境或小批量确认能转换、能跑通；真遇到 OOM 就把并行数调小，需要几千上万环境再考虑更大显存或多卡。

**检查方法**：把模型 `mjx.put_model` 转换、再跑一步，这两步任一报错就说明用到了不支持的特性（像 cylinder 配对这类，在 `put_model` 阶段就会抛错，错误信息会指明具体是哪一对 geom）。

## 实测：对一批 menagerie 机器人跑 put_model

照上面的方法，把 `mjx.put_model` 在一批 menagerie 机器人上各跑一遍（脚本 `labs/04-simulation/mjx_limitations.py`，日志 `runs/04-simulation/mjx_limitations.txt`），结果如下（状态摘自该日志，`#` 后为注解）：

```text
franka_emika_panda     mjx_ok       # 含 tendon 夹爪，tendon 确实已支持
universal_robots_ur5e  mjx_ok
kuka_iiwa_14           mjx_ok
unitree_a1             mjx_ok
unitree_go2            mjx_failed   # NotImplementedError: cylinder×box 未实现
anybotics_anymal_b     mjx_failed   # 同上：cylinder×box
anybotics_anymal_c     mjx_failed   # 同上：cylinder×box
robotis_op3            mjx_ok
aloha                  mjx_ok
google_robot           mjx_failed   # cylinder×mesh 未实现
trs_so_arm100          mjx_ok
```

带 tendon 的 Panda 能过（印证 tendon 已支持），而 go2 / anymal / google_robot 都栽在 cylinder 的碰撞**配对**上（go2/anymal 是 `cylinder`×`box`、google_robot 是 `cylinder`×`mesh`），正是上表“部分碰撞几何对”那一行的实例。（`put_model` 是模型转换检查，结果与 GPU 型号无关。）

## 数值差异与陷阱

前面[最小迁移](02-minimal-migration.md)那页已经提过 CPU 和 MJX 有微小浮点差异。这里补充几个需要特别留意的地方：

- **接触行为**：由于求解器的数值差异，CPU 和 MJX 在接触密集的场景（如抓取、堆叠）中可能会有更明显的轨迹分岔。同一个抓取动作在 CPU 上能夹住、在 MJX 上可能滑落（或反过来）。
- **确定性**：MJX 在 GPU 上的计算是确定性的（给定相同输入和相同 GPU 架构），但不同 GPU 架构（如 A100 vs V100）上可能产生不同结果。这和 CPU 上跨架构的浮点差异类似。
- **随机种子**：MJX 的随机性由 JAX 的 PRNG key 控制，和 numpy 的 `np.random` 是两套系统。迁移时别忘了把随机数部分也改过来。

## MuJoCo Warp 简介

MuJoCo Warp 是 NVIDIA 主导的另一个 GPU 后端。它使用 Warp（NVIDIA 的 Python→CUDA 编译框架）来实现 MuJoCo 的物理流水线。

和 MJX 的关键差异：

| | MJX | MuJoCo Warp |
|---|---|---|
| 核心语言 | JAX（Python → XLA → GPU） | Warp（Python 子集 → CUDA） |
| 硬件支持 | NVIDIA GPU、AMD GPU（via JAX）、TPU | NVIDIA GPU（CPU 仅供开发调试） |
| API 风格 | JAX 纯函数式 | 更接近原生 MuJoCo（有状态） |
| 生态集成 | Brax（训练）、JAX 生态 | Isaac Sim / Isaac Lab 生态 |
| 发展速度 | 稳定迭代 | 快速迭代中 |
| 安装 | `pip install mujoco-mjx` | `pip install mujoco-warp` |

MuJoCo Warp 仍在快速迭代：截至写作时已能直接 `pip install mujoco-warp`，但还处于早期阶段，仍以 NVIDIA GPU 为主，官方也提示超过约 60 个自由度的场景性能会明显下降。生态上有一个值得留意的信号：训练框架 MuJoCo Playground 现已同时支持 MJX 和 MuJoCo Warp 两种后端，可以看作两个后端在真实训练里的对照。

## 三种后端的选型建议

<figure class="doc-figure" aria-label="后端选型">
  <p class="doc-figure-title">原生 / MJX / Warp 选型指南</p>
  <table>
    <tr><th>场景</th><th>推荐</th><th>理由</th></tr>
    <tr><td>单环境调试、控制实验</td><td>原生 MuJoCo</td><td>最完整、最稳定、最易用</td></tr>
    <tr><td>RL 训练（< 32 并行）</td><td>原生 + Gymnasium VecEnv</td><td>改动最小，CPU 够用</td></tr>
    <tr><td>RL 训练（256-4096 并行）</td><td>MJX + Brax</td><td>GPU 加速显著，生态完善</td></tr>
    <tr><td>需要 flex / 可变形体 + 大规模并行</td><td>原生（CPU 多线程）</td><td>MJX 暂不支持可变形体，先用 CPU 顶上</td></tr>
    <tr><td>NVIDIA Isaac 生态深度用户</td><td>MuJoCo Warp</td><td>和 Isaac 生态集成更好</td></tr>
    <tr><td>TPU 环境</td><td>MJX</td><td>JAX 原生支持 TPU</td></tr>
  </table>
</figure>

三条简单经验法则：
1. **调试和开发阶段用原生**，改动最小、反馈最快。
2. **训练阶段看并行度**，< 32 环境不需要 MJX，> 256 环境 MJX 价值显著。
3. **模型用到了 MJX 不支持的特性就别强上**，回 CPU 或者考虑 Warp。

## 小结

- MJX 是 MuJoCo 的子集（flex、部分 sensor 等尚不支持，但 tendon/equality 已支持），用之前先跑一步测试。
- CPU 和 MJX 有微小浮点差异，RL 场景中通常不影响策略性能。
- MuJoCo Warp 是 NVIDIA 主导的替代方案，和 Isaac 生态更紧密。
- 选型原则：调试用原生、小规模用 VecEnv、大规模用 MJX、特殊需求看 Warp。

## 参考资料

- [MuJoCo Documentation: MJX（Feature Parity / limitations）](https://mujoco.readthedocs.io/en/stable/mjx.html)
- [MuJoCo Documentation: MJWarp](https://mujoco.readthedocs.io/en/latest/mjwarp/)：安装、硬件要求与 60 DoF 性能提示的官方来源
- [MuJoCo Warp（GitHub）](https://github.com/google-deepmind/mujoco_warp)
- [MuJoCo Playground（GitHub）](https://github.com/google-deepmind/mujoco_playground)：同时支持 MJX 与 MuJoCo Warp 的训练框架
- [MuJoCo Menagerie（含 mjx 简化碰撞变体）](https://github.com/google-deepmind/mujoco_menagerie)

## 导航

- 上一节：[速度与 benchmark](03-speed-and-benchmarks.md)
- 返回上级：[MJX 与 GPU 并行](../07-mjx-and-gpu.md)
- 下一节：[训练教程](../08-training-recipes.md)
