# 速查与练习

这一页不讲新概念，而是把本组页面里最常用的 API、字段和检查问题集中放在一起。真正写代码时，读者不一定记得每个 shape 或 wrapper 的细节，可以回到这里快速查。

## 最小创建环境

```python
import gymnasium as gym
import mani_skill.envs

env = gym.make(
    "PickCube-v1",
    obs_mode="state",
    control_mode="pd_ee_delta_pose",
    render_mode="rgb_array",
    num_envs=1,
)
obs, info = env.reset(seed=0)
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
env.close()
```

`import mani_skill.envs` 负责注册 ManiSkill 内置任务。少了这一行，`gym.make("PickCube-v1")` 可能找不到环境。

## 常用参数速查

| 参数 | 作用 | 本节主线取值 |
|---|---|---|
| `env_id` | 选择任务 | `PickCube-v1` |
| `obs_mode` | 选择观测结构 | `state`、`rgbd` |
| `control_mode` | 选择 action 语义 | `pd_ee_delta_pose` |
| `reward_mode` | 选择奖励形式 | dense / sparse 等 |
| `render_mode` | 选择 `env.render()` 输出 | `rgb_array` |
| `num_envs` | 并行环境数量 | `1` 或 `16` |

## 本节真实产物速查

| 产物 | 关键信息 |
|---|---|
| `maniskill_pickcube_summary.json` | state 观测 `(1, 42)`、动作 `(7,)`、success 子条件、control mode 对比 |
| `maniskill_pickcube_spaces.txt` | `observation_space`、`action_space`、single space |
| `maniskill_pickcube_vector.json` | `num_envs=16`、`obs_shape=[16, 42]`、`reward_device="cuda:0"` |
| `maniskill_pickcube_wrapper.txt` | `CPUGymWrapper` 后 obs `(42,)`，reward / success 为普通标量 |
| `maniskill_pickcube_reset.png` | `env.render()` 画面 |
| `maniskill_pickcube_rgb.png` | `rgbd` 观测中的 RGB |
| `maniskill_pickcube_depth.png` | `rgbd` 观测中的 depth 可视化 |
| `maniskill_pickcube_rollout.mp4` | 随机动作 rollout 视频 |

## 常见 shape 速查

| 场景 | 常见形状 | 怎么理解 |
|---|---|---|
| `num_envs=1, obs_mode="state"` | `(1, 42)` | 前面的 `1` 是 batch 维 |
| `num_envs=16, obs_mode="state"` | `(16, 42)` | 16 个环境并行，每个环境 42 维 state |
| `pd_ee_delta_pose` | `(7,)` 或 `(N, 7)` | 末端位姿增量 + 夹爪控制 |
| `CPUGymWrapper` 后的 state | `(42,)` | 去掉单环境 batch 维 |
| `rgbd` 里的 RGB | `(1, H, W, 3)` | batch + 图像高宽通道 |
| `rgbd` 里的 depth | `(1, H, W, 1)` | batch + 单通道深度 |

## 易错点速查

| 现象 | 第一反应 |
|---|---|
| `gym.make("PickCube-v1")` 找不到环境 | 是否漏了 `import mani_skill.envs` |
| 看到 `(1, 42)` | 这是 batch 维，不是状态多了一维 |
| 随机 rollout 失败 | 正常；随机动作不是成功策略 |
| 视频能播放但视觉策略报错 | 检查 `obs["sensor_data"]`，不要只看 `env.render()` |
| reward 变大但 success 仍 false | reward 和 success 不是同一件事 |
| GPU 存在但 vector probe 不在 GPU | 看 `reward_device`，不要只看 `nvidia-smi` |
| wrapper 后 shape 变了 | wrapper 可能去掉 batch 维，要重新检查 space |

## 动手练习

1. 把 `obs_mode` 从 `state` 改成 `rgbd`，打印 `obs.keys()` 和每个子项 shape。判断哪些数据适合进入策略，哪些数据适合做相机几何计算。
2. 把 `control_mode` 分别改成 `pd_joint_pos`、`pd_joint_delta_pos`、`pd_ee_delta_pos`、`pd_ee_delta_pose`，记录 action space 的变化。思考为什么末端控制和关节控制维度不同。
3. 用 `num_envs=1` 和 `num_envs=16` 各跑一次 vector probe，对比 observation、reward 和 done 的 shape。解释为什么网络输入不应该写死成 16。
4. 给 `num_envs=1` 环境套上 `CPUGymWrapper`，比较 wrapper 前后的 observation、reward、terminated、truncated、success 类型。
5. 只看 rollout 视频写一句“任务现象”；再只看 `summary.json` 写一句“接口证据”。比较这两句话有什么不同。

## 导航

- 上一页：[任务内部怎么读](08-read-a-task.md)
- 返回上级：[ManiSkill 任务接口与 PickCube 实战](../01-maniskill-task-interfaces.md)
- 下一节：[其他仿真生态](../../06-other-simulation-ecosystems.md)
