# 模型调度源码

SP-VLA 的调度逻辑集中在 `prismatic/extern/hf/modeling_prismatic.py` 的 `OpenVLAForActionPrediction` 里，入口是 `predict_action()`。它每步先算触发条件，满足就走 `fit_next_action()` 外推、跳过完整前向，否则跑 `self.generate()` 并把速度写给剪枝模块。本页按这条链给出动作缓冲、跳步判据、Ridge 生成器的实现与默认值。

## 本节目标

理解动作缓冲怎么维护、跳步的两个条件各判什么、Ridge 生成器如何外推平移并处理夹爪，以及 `step_skip`、`z_xy_rate_skip`、`z_max_skip`、τ 各控制什么。

## 动作缓冲与触发条件

`save_actions()` 维护一个定长为 `save_action_number`（默认 6）的动作缓冲，并记录每个动作是 VLA 生成的还是外推得到的。`fit_action_flag` 就是架构页里 $N_G/N_A>\tau$ 的条件，这里 $\tau$ 取 $4/6$：缓冲里至少 4 步是 VLA 真正生成的，才允许后续外推。

```python
def save_actions(self, actions, generate=True):
    self.total_actions.append(copy.deepcopy(actions))
    self.total_actions_type.append("generate" if generate else "fit")

    if len(self.total_actions) > self.save_action_number:   # 缓冲满 6 步后滑动
        self.total_actions.pop(0)
        if self.total_actions_type.pop(0) == "generate":
            self.save_generate_step -= 1                     # 移出的是生成动作，计数减一

    if generate:
        self.save_generate_step += 1

    # 缓冲里 VLA 生成动作占比达到 4/6 才允许跳步，避免连续外推积累误差
    self.fit_action_flag = self.save_generate_step / self.save_action_number >= 4/6
```

外推动作以 `generate=False` 存回缓冲，会降低 `save_generate_step`。连续跳步几步后占比跌破 $4/6$，`fit_action_flag` 变假，强制下一步回到完整前向补一个真实动作，缓冲因此不会长期靠外推维持。

## 调度器：跳步还是推理

`predict_action()` 先从缓冲末尾算平移，判断最近若干步是否都是平滑的水平移动。`translation_flag` 要求连续 `step_skip` 步都满足两个条件：竖直分量与水平分量之比小于 `z_xy_rate_skip`、且竖直绝对位移小于 `z_max_skip`。任一步不满足就不跳：

```python
translation_flag = False
if len(self.total_actions) >= self.cfg.step_skip:
    for i in range(1, self.cfg.step_skip + 1):
        max_xy = max(abs(self.total_actions[-i][0]), abs(self.total_actions[-i][1]), 0.0001)
        max_z = abs(self.total_actions[-i][2])
        # 竖直相对水平够小、竖直绝对位移够小 -> 平滑水平过渡
        translation_flag = max_z / max_xy < self.cfg.z_xy_rate_skip and max_z < self.cfg.z_max_skip
        if not translation_flag:
            break
```

两个条件都满足、且缓冲里生成动作占比达标时走跳步路径，用 `fit_next_action()` 外推并以 `generate=False` 存回；否则走完整前向：跑 `self.generate()` 解出约 7 个动作 token 并反归一化，同时把这一步的竖直平移写进 `cfg.z_trans` 供剪枝模块用。

```python
if self.fit_action_flag and translation_flag:
    self.cfg.skip_flag = 1
    actions = self.fit_next_action(self.total_actions)      # 跳步：Ridge 外推
    self.save_actions(actions, generate=False)
else:
    self.cfg.skip_flag = 0
    self.cfg.z_trans = abs(self.total_actions[-1][2]) if self.total_actions else 0  # 传给剪枝
    generated_ids = self.generate(input_ids, max_new_tokens=self.get_action_dim(unnorm_key), **kwargs)
    # ... 解码动作 token、反归一化得到 actions ...
    self.save_actions(actions, generate=True)
```

`cfg.z_trans` 只在完整前向这条分支更新，是上一次真实动作的竖直位移。剪枝模块据此定当前帧的剪枝比例，因此调度和剪枝共享同一个速度信号。

## 轻量生成器

`fit_next_action()` 是 Ridge 回归外推。它只取缓冲里动作的前三维（$x,y,z$ 平移），以时间下标为自变量 $\mathbf{X}=[\,t\ \ 1\,]$，解带正则的最小二乘得系数、外推到下一时刻。`lambda_reg` 取 $10^{-4}$，几乎只做数值稳定、不明显收缩解：

```python
def fit_next_action(self, total_actions):
    total_actions = np.array(total_actions)
    actions = total_actions[:, :3]                          # 只取 x,y,z 平移
    X = np.arange(len(actions)).reshape(-1, 1)
    X = np.hstack([X, np.ones_like(X)])                     # [t, 1]
    Y = actions

    lambda_reg = 1e-4
    Beta = np.linalg.solve(X.T @ X + lambda_reg * np.eye(2), X.T @ Y)   # 闭式解
    next_action = Beta[0] * len(actions) + Beta[1]          # 外推下一步
    next_action = np.clip(next_action, -0.9, 0.9)           # 限制到合理动作范围

    # 单步增量不超过历史最大增量，抑制外推越界
    delta_max = np.max(np.abs(np.diff(Y, axis=0)), axis=0)
    delta = np.clip(next_action - Y[-1], -delta_max, delta_max)
    next_action = Y[-1] + delta

    next_gripper_state = total_actions[-1, 3:]              # 夹爪状态沿用上一步
    return np.hstack([next_action, next_gripper_state])
```

外推后有两层约束。一层把每维裁到 $[-0.9,0.9]$，落进正常动作范围。另一层把这步相对上一步的增量裁到历史最大增量之内，避免线性外推在拐点处外推出过大的跨步。夹爪维不参与回归，直接复制上一步状态，把外推限制在连续平移上。

## 可调参数

调度行为由这几个参数控制，实际取值以 `run_libero.py` 里各套件的设置为准：

| 参数 | 含义 | 默认 / 示例 | 调大 / 调小的影响 |
| --- | --- | --- | --- |
| `step_skip` | 判定平滑过渡要连续满足的步数 | libero_spatial 为 1，其余套件为 2 | 调大要求更长的连续平滑段才跳步，更保守、跳步更少 |
| `z_xy_rate_skip` | 竖直/水平比阈值 | 0.4–1.2（按套件） | 调大更容易判为水平过渡、跳步更多；调小更严 |
| `z_max_skip` | 竖直绝对位移阈值 | 0.3–0.5（按套件） | 调大放宽竖直位移限制、跳步更多；调小更严 |
| τ（`save_generate_step` 占比） | 允许跳步所需的 VLA 生成动作占比 | 4/6（硬编码） | 提高要求更多真实动作、外推更少更稳；降低外推更多但易漂移 |

## 加速贡献

调度是 SP-VLA 里最有效的单项。消融中单独开模型调度能到约 1.27× 加速、精度仅降约 1 个百分点，说明连续控制里过渡步占比高、大量完整前向可以由外推替代（论文报告）。单独开 token 剪枝的加速更小，且 VLA 对 token 更敏感、精度下降更明显；两者叠加才得到 LIBERO 上 1.35×–1.50× 的整体加速。

## 本页小结

- `save_actions()` 维护定长 6 的动作缓冲，`fit_action_flag = save_generate_step/6 >= 4/6` 即 $N_G/N_A>\tau$，外推动作会降低占比、强制回到完整前向补真实动作。
- `predict_action()` 的 `translation_flag` 要求连续 `step_skip` 步满足竖直/水平比小于 `z_xy_rate_skip` 且竖直位移小于 `z_max_skip`；跳步走 `fit_next_action`，否则跑 `self.generate` 并把 `cfg.z_trans` 写给剪枝。
- `fit_next_action()` 用 Ridge 闭式解只外推 $x,y,z$，裁到 $[-0.9,0.9]$、增量裁到历史最大值，夹爪沿用上一步。
- 调度单项消融约 1.27×、精度降约 1%，是整体加速的主要来源。

## 导航

- 上一节：[整体架构](02-architecture.md)
- 返回上级：[SP-VLA](../03-sp-vla.md)
- 下一节：[token 剪枝源码](04-token-pruning.md)
