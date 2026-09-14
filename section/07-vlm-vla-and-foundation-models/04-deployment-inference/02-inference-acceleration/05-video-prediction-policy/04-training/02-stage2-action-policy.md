# 第二阶段动作策略训练

目标：理解第二阶段到底训练了哪些模块、视频模型在这里扮演什么角色、CALVIN 与 xbot 分支有什么差异。

## 第二阶段入口

主要有两条线：

- CALVIN：`step2_train_action_calvin.py`
- xbot / xhand：`step2_train_action_xbot.py`

这两条线共享方法思想，但数据接口和动作定义不完全一样。

## 第二阶段的主逻辑

从 `policy_models/VPP_policy.py` 角度看，第二阶段大致在做：

1. 编码语言
2. 从第一阶段视频模型抽中间特征
3. 用 `Video Former` 做时空聚合
4. 用条件动作扩散头输出多步动作

也就是说，第二阶段并不是从头重新学视觉，而是在“消费第一阶段给出的 predictive features”。

如果从论文第 4.2 节来理解，这一步其实包含两个核心设计：

1. 把 TVP 模型当作视觉编码器，而不是完整视频去噪器
2. 用动作扩散策略在 predictive representations 上学习隐式逆动力学

## 真正训练的是哪些模块

常见情况是：

- 视频模型大部分被冻结
- `Video Former` 等聚合器是重点训练对象
- 动作扩散头是重点训练对象

这也是为什么如果第一阶段表征质量太差，第二阶段往往很难完全靠动作头自己补回来。

论文里这部分通常可以理解成“三段式参数职责”：

- TVP 模型：提供未来感表征
- `Video Former`：把高维时空特征压缩成少量 token
- Diffusion Policy Head：根据 token、语言和状态输出动作

也就是说，第二阶段的学习重点主要落在“如何压缩并消费未来表征”，而不是重新学习底层视觉。

## CALVIN 和 xbot 分支差在哪里

| 方面 | CALVIN | xbot / xhand |
|---|---|---|
| 动作维度 | 常见是 7 | 常见更高 |
| 数据接口 | benchmark 风格更强 | 自定义 JSON 和状态定义更多 |
| 评测方式 | 闭环 benchmark | 离线验证和真机模板更多 |
| 归一化 | 更依赖数据模块 | 更依赖手工统计量 |

从论文角度看，CALVIN 对应的是标准化 benchmark 路线，更适合验证方法本身；而 xbot / xhand 这类分支更接近作者把同一方法迁移到真实机器人和高维手部控制的工程实现。

## 第二阶段看哪些字段最关键

优先看：

- `action_dim`
- `obs_seq_len`
- `act_seq_len`
- `num_latents`
- `use_Former`
- `use_all_layer`
- `extract_layer_idx`

这些字段决定了：

- 取哪一层视频特征
- 用什么方式聚合
- 最终输出多少步动作

如果把这些字段和论文设计一一对应，可以更容易理解：

- `use_all_layer`：是否聚合多层 predictive features
- `extract_layer_idx`：只取单层时，取哪一层
- `num_latents`：`Video Former` 输出多少 token
- `act_seq_len`：一次动作扩散预测多长的 action chunk
- `obs_seq_len`：当前输入使用多少步观测

论文的消融实验说明：

- 多层特征聚合优于只取最终单层特征
- `Video Former` 不仅影响精度，也明显影响推理效率
- one-step predictive representation 已经足够有效

## 为什么第二阶段可以看作“隐式逆动力学”

这是论文最值得解释清楚的一点。

普通 inverse dynamics 常写成：

- 给定当前状态和下一状态
- 预测中间应该执行什么动作

VPP 没有显式提供一个干净的“下一状态标签”，而是提供了一组视频模型内部的未来表征。作者的观点是：

- 这些表征里已经包含“机器人将朝哪里移动、物体将怎样变化”的趋势
- 动作策略只需要学会让当前观测朝这种趋势推进

因此，它学到的是一种**条件在 predictive representation 上的隐式 inverse dynamics**。这也是论文标题里 “Policy with Predictive Visual Representations” 的真正含义。

## 小结

- 第二阶段的本质不是“再训一个普通 policy”，而是“让 policy 学会使用未来表征”。
- `Video Former` 和动作扩散头共同决定了这些未来表征如何被消费。
- CALVIN 和 xbot 的差异主要不在论文，而在工程接口。

## 导航

- 上一节：[第一阶段视频模型训练](01-stage1-video-model.md)
- 返回上级：[训练视频模型与动作策略](../04-training.md)
- 下一节：[CALVIN 评测与排障](03-calvin-evaluation-and-pitfalls.md)
