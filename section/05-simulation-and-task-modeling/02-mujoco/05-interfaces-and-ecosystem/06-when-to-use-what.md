# 接口选择

到这里，我们已经见过四种用 MuJoCo 的方式：**原生 mujoco**、**dm_control**、**Gymnasium 风格包装**、**MJX**（面向 GPU 的批量版本，本单元后面的 [MJX 与 GPU 并行](../07-mjx-and-gpu.md) 一节详讲）。它们能力上有不少重叠，又各有侧重，刚上手容易拿不准选哪个。

## 本节目标

本节就来理清怎么选：

1. 这四种接口各自牺牲什么、得到什么？
2. 做控制实验、训练 RL 策略、大规模并行采样这几类需求下，通常偏向哪一个？

## 四种接口的对比

| | 原生 mujoco | dm_control | Gymnasium | MJX |
|---|---|---|---|---|
| 学习曲线 | 低 | 中 | 中 | 中-高 |
| API 风格 | MuJoCo 原生 | DeepMind RL 风格 | 标准 gym 接口 | JAX 函数式 |
| 预定义任务 | 无 | suite（几十个经典任务） | gymnasium MuJoCo 环境 | 无（需自行适配） |
| 自定义任务 | 自由（但需自己写全套） | composer（结构化搭建） | 继承 gym.Env | 适合批量环境 |
| 并行能力 | 需手写多线程 | 有限 | VectorEnv（CPU，~16 并行） | GPU 数千并行 |
| 生态兼容 | 专有 | dm_control 生态 | SB3/RLlib/CleanRL 等 | JAX/Brax 生态 |
| 适合场景 | 理解物理、控制研究 | 评测算法、结构化任务 | 用 RL 框架训练 | 大规模批量训练 |

## 决策场景 1：理解物理、自定义模型、做控制实验

**推荐：原生 mujoco。**

理由：这是离 MuJoCo 最近的一层，没有额外的抽象包装，能直接接触到 `mjModel`、`mjData`、`mj_step` 的完整行为。前面几部分讲的就是这一层。当需要精确控制每一个关节、理解 actuator 的 ctrl 是怎么变成力的、调试接触参数时，原生接口往往最直接。

## 决策场景 2：训练 RL 策略

**推荐：Gymnasium 环境 + Stable-Baselines3（小规模），MJX + Brax（大规模；Brax 是 JAX 原生的 RL 训练库）。**

理由：大多数 RL 训练框架天然适配 Gymnasium 接口。可以用 gymnasium 内置的 MuJoCo 环境（如 Ant-v5），也可以把自己的 MJCF 包装成 `gym.Env`。训练代码和框架文档里写的基本一致。

当单个环境的实验跑通后，如果需要扩容到几千个并行环境来加速训练（比如 PPO 需要大量 on-policy 样本），再考虑迁移到 MJX + Brax。

## 决策场景 3：评测算法在经典任务上的表现

**推荐：dm_control suite。**

理由：dm_control 的 suite 是社区广泛使用的标准评测集。当需要和其他论文里的结果做对比（比如"我们的算法在 humanoid:walk 上跑了多少分"），用同一个评测平台才能公平比较。

## 一张总览图

<figure class="doc-figure" aria-label="接口选择决策">
  <p class="doc-figure-title">从需求出发选择接口</p>
  <div class="figure-pipeline">
    <div class="figure-node tone-green">
      <strong>想理解 MuJoCo 本身？</strong>
      <span>→ 原生 mujoco</span>
    </div>
    <div class="figure-node tone-blue">
      <strong>要跑经典 RL 任务？</strong>
      <span>→ dm_control suite</span>
    </div>
    <div class="figure-node tone-gold">
      <strong>要用 SB3/RLlib 训练？</strong>
      <span>→ Gymnasium</span>
    </div>
    <div class="figure-node tone-rose">
      <strong>要批量训练几千环境？</strong>
      <span>→ MJX + Brax（本单元 MJX 一节）</span>
    </div>
    <div class="figure-node tone-green">
      <strong>要从零搭一个多实体任务？</strong>
      <span>→ dm_control composer</span>
    </div>
  </div>
</figure>

## 小结

- 这几种接口不是互斥的，实际项目中经常会混用（比如用 composer 定义任务，包成 Gymnasium 给 SB3 训练，底层偶尔直接调 MuJoCo API 做调试）。
- 一个稳妥的路径是从原生 MuJoCo 入门、理解基础，再按"用什么框架训练"来决定上层接口。
- 不必一开始就追求"最正确"的选择，先跑起来往往更重要。

## 参考资料

- [dm_control（GitHub）](https://github.com/google-deepmind/dm_control)
- [Gymnasium Documentation](https://gymnasium.farama.org/)
- [MuJoCo Documentation: MJX](https://mujoco.readthedocs.io/en/stable/mjx.html)

## 导航

- 上一节：[Gymnasium 风格包装](05-gymnasium-wrappers.md)
- 返回上级：[接口与生态](../05-interfaces-and-ecosystem.md)
- 下一节：[抓取实战](../06-grasping-walkthrough.md)
