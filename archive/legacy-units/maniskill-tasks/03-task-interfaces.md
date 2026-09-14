# 任务的五把钥匙：env_id、观测、控制、奖励与成功

把环境跑起来以后，下一步不是马上训练策略，而是先看清任务接口。一个 ManiSkill 任务，通常由几类设置共同决定：任务是谁，策略能看到什么，动作是什么意思，奖励怎么给，成功条件怎么判断。

## 本节目标

本节围绕下面几个问题展开：

1. `env_id`、`obs_mode`、`control_mode`、`reward_mode` 和 `success` 各自决定任务的哪一部分。
2. `gym.make` 背后发生了什么，每一层对初学者意味着什么。
3. 不同 `control_mode` 下动作空间的维度和语义会怎样变化，为什么换了控制模式后不能直接横比成功率。
4. `reward` 和 `info["success"]` 分别应该用来做什么，它们的职责为什么不能混。

## 一个任务的五个入口

本节先把接口整理成一张表：

| 设置 | 它决定什么 | 在 `PickCube-v1` 里回答的问题 |
|---|---|---|
| `env_id` | 当前任务 | 是抓方块，还是开抽屉、推物体 |
| `obs_mode` | 观测空间 | 策略看到状态向量、RGB-D，还是点云 |
| `control_mode` | 动作空间 | 动作是关节目标、关节增量，还是末端位姿增量 |
| `reward_mode` | 奖励信号 | 训练时用稀疏奖励、稠密奖励，还是归一化稠密奖励 |
| `success` | 成功判定 | 任务是否真的完成，从 `info` 里读 |

其中 `obs_mode` 和 `control_mode` 会直接改变 Gymnasium 的空间。写策略网络之前，应先打印 `observation_space` 和 `action_space`，不要凭经验猜输入输出维度。

```python
import gymnasium as gym
import mani_skill.envs

env = gym.make(
    "PickCube-v1",
    num_envs=1,
    obs_mode="state",
    control_mode="pd_ee_delta_pose",
)

print("observation_space:", env.observation_space)
print("action_space:", env.action_space)
env.close()
```

输出是：

```text
observation_space: Box(-inf, inf, (1, 42), float32)
action_space: Box(-1.0, 1.0, (7,), float32)
```

这说明当前策略输入是 42 维状态，外面再包一层 batch 维；动作是 7 维，含末端位姿增量和夹爪控制。

## 控制模式：动作维度和动作语义会一起变

`control_mode` 不是一个小配置。它会改变动作空间的维度，也会改变动作每一维的含义。

本机对几个常见控制模式的输出如下：

| `control_mode` | 动作含义 | 输出空间 |
|---|---|---|
| `pd_joint_pos` | 直接给各关节目标位置 | `(8,)`，带各维上下界 |
| `pd_joint_delta_pos` | 给各关节位置增量 | `Box(-1.0, 1.0, (8,), float32)` |
| `pd_ee_delta_pos` | 给末端位置增量，加夹爪 | `Box(-1.0, 1.0, (4,), float32)` |
| `pd_ee_delta_pose` | 给末端位姿增量，加夹爪 | `Box(-1.0, 1.0, (7,), float32)` |

其中 `pd` 表示底层使用 PD 控制器跟踪目标；`delta` 表示动作给的是相对当前状态的增量，不是绝对目标。对操作任务来说，增量式末端控制比较常见，因为它比直接给关节绝对目标更接近"夹爪往哪里动一点"的直觉。

> ⚠️ **易错点**：换了 `control_mode`，就不能直接拿两个策略的成功率横比。末端 7 维动作和关节 8 维动作不是同一个动作接口。要比较策略能力，应先固定任务、观测、控制和奖励设置。

## 奖励与 success：训练信号和完成判定要分开看

`reward_mode` 决定 `step()` 返回的 reward 长什么样。常见选择包括：

| `reward_mode` | 含义 | 适合场景 |
|---|---|---|
| `sparse` | 只在成功时给明显奖励 | 成功判定清楚，但学习难 |
| `dense` | 按距离、抓取、放置等子目标给塑形奖励 | 更利于学习，但任务相关性强 |
| `normalized_dense` | 将 dense 奖励归一化 | 训练时更容易处理数值尺度 |
| `none` | 不返回有效奖励 | 只关心回放或成功统计时使用 |

reward 是训练信号，`success` 是任务完成事实。两者不要混在一起。`PickCube-v1` 的 `info` 里除了 `success`，还有若干子条件：

```text
elapsed_steps
is_grasped
is_obj_placed
is_robot_static
reconfigure
success
```

这几个键把任务拆得很清楚：方块有没有被抓住，是否放到目标附近，机器人是否停稳，最后再合成 `success`。这样做的好处是，调 reward 不会顺手改变"什么算成功"。

> ⚠️ **易错点**：不要用 reward 的大小来判断任务是否完成。reward 是训练引导信号，其数值大小和任务设计有关；成没成只看 `info["success"]`。

## 小结

- 一个 ManiSkill 任务主要由 `env_id`、`obs_mode`、`control_mode`、`reward_mode` 和 `info["success"]` 共同决定。
- 写策略前应先打印 `observation_space` 和 `action_space`，不要凭任务名猜输入输出。
- `control_mode` 会同时改变动作维度和语义，控制模式不同的结果不能直接横向比较。
- reward 是训练引导信号，success 是完成判定，两者应该分开读。
- `info` 里的子条件（`is_grasped`、`is_obj_placed`、`is_robot_static` 等）有助于定位失败原因，不应只看最终 `success`。

## 导航

- 上一节：[跑通 PickCube-v1：最小闭环](02-pickcube-first-run.md)
- 返回上级：[ManiSkill 任务环境](../01-maniskill-tasks.md)
- 下一节：[观测与渲染：state、rgbd 与运行截图](04-observation-and-rendering.md)
