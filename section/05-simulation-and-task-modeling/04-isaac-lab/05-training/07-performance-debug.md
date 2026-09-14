# 性能优化与调试

训练出问题时，不要一上来就改算法。先判断问题属于哪一类：任务定义错、训练配置错、性能瓶颈，还是可视化误判。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-debug-funnel.svg" alt="Isaac Lab 训练排障漏斗" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">排障顺序从任务闭环开始：环境能跑、观测含目标、动作生效、奖励分项变化，再到 PPO 超参。</figcaption>
</figure>

## 本节目标

本节围绕下面几个问题展开：

1. reward 不涨时，按什么顺序排查（任务闭环优先于算法超参）？
2. 行为异常为什么要看视频而不是只看曲线？
3. 吞吐低怎么区分 GPU / CPU / 显存 / 渲染瓶颈？
4. 显存爆掉、传感器瓶颈分别怎么处理？

## reward 不涨的排查顺序

```text
1. play 随机策略，看环境是否能正常 reset / step
2. 检查 observation 是否含目标信息
3. 检查 action 是否真的控制到关节
4. 检查 reward 分项是否有非零变化
5. 检查 termination 是否过早触发
6. 降低随机化，跑最简单版本
7. 再调 PPO 超参
```

前五步都属于任务问题，不是算法问题。

## 行为异常看视频

曲线只能说明数值变化，视频才能说明行为。

训练时录制：

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-Velocity-Flat-Unitree-Go2-v0 \
    --headless \
    --enable_cameras \
    --video \
    --video_length 200 \
    --video_interval 5000
```

启用录像会明显降低吞吐。调试阶段少量环境录，正式长训再关掉。

## 吞吐低怎么查

先看 `steps per second` 和 GPU 状态：

```text
GPU 利用率高，显存未满：可能 num_envs 还可增加
GPU 利用率低，CPU 高：可能 Python / wrapper / 数据搬运瓶颈
显存接近满：减少 num_envs 或传感器分辨率
启用相机后骤降：渲染瓶颈
```

关键参数：

| 参数 | 影响 |
|---|---|
| `num_envs` | 采样并行度和显存 |
| `decimation` | 策略频率和物理步数 |
| `sim.dt` | 物理步长 |
| `sensor.update_period` | 传感器更新频率 |
| camera resolution | 渲染显存和吞吐 |

## num_envs 调法

调试：

```text
16-64 个环境，开 GUI 或视频
```

正式训练：

```text
纯状态任务：尽量提高到 GPU 吃满
带相机任务：从小环境数和低分辨率开始
```

不要用正式训练的 `num_envs` 调 reward。环境太多时，观察和定位问题反而困难。

## 传感器瓶颈

相机是最常见瓶颈：

| 做法 | 效果 |
|---|---|
| 降低分辨率 | 降显存、提吞吐 |
| 增大 `update_period` | 降渲染频率 |
| 减少相机数量 | 直接降开销 |
| 用 TiledCamera | 大量相机时更高效 |
| 调试时关相机 | 判断瓶颈是否来自视觉 |

RayCaster 和 ContactSensor 通常比相机便宜，但射线数量过多也会影响速度。

## 显存问题

显存爆掉时按顺序处理：

```text
1. 减 num_envs
2. 降相机分辨率和数量
3. 检查 USD 是否 instanceable
4. 简化碰撞体和网格
5. 减少传感器历史长度
```

自定义机器人如果不是 instanceable，几百或几千环境会迅速放大显存问题。

## 可视化标记

`VisualizationMarkers` 可用于显示目标点、命令方向、末端位置等，不参与物理。

```python
import isaaclab.sim as sim_utils
from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg

marker_cfg = VisualizationMarkersCfg(
    markers={
        "target": sim_utils.SphereCfg(radius=0.05),
    }
)
markers = VisualizationMarkers(marker_cfg)
markers.visualize(translations=target_positions)
```

debug 可视化能快速发现目标采样、坐标系和命令方向是否正确。

## 常见问题表

| 现象 | 先查 |
|---|---|
| reward 一直为 0 | reward 函数是否返回非零，目标是否进入 observation |
| episode 很短 | termination 是否过早触发 |
| 策略不动 | 动作尺度、actuator、惩罚权重 |
| 策略抖动 | action scale、stiffness / damping、action_rate 奖励 |
| 视频行为和曲线不一致 | reward hacking，查看分项奖励 |
| steps/s 很低 | 相机、CPU、num_envs、传感器频率 |
| 训练中 OOM | 显存、相机、instanceable、num_envs |

## 用 `--video` 录训练视频

排查“视频行为和曲线不一致”这类问题时，最直接的办法是在训练时定期录像。给 `train.py` 加 `--video`（脚本检测到后会自动 `enable_cameras=True`），它会按 `--video_interval` 周期触发、每段录 `--video_length` 步，全程不需要 GUI：

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-Cartpole-v0 --headless --video --video_length 100 --video_interval 2000
```

启动时会打印录像配置：

```text
[INFO] Recording videos during training.
        video_folder: .../logs/rsl_rl/cartpole/<run>/videos/train
        step_trigger: lambda step: step % args_cli.video_interval == 0
        video_length: 100
        disable_logger: True
```

录得的训练片段（headless 下纯靠相机离屏渲染产出 mp4）：

<video src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-perf-debug-cartpole-video.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

> 注意：有些版本或驱动环境下，纯 `--headless` 不加相机时再走渲染路径，可能遇到 `carb.tasking ... Recursion not allowed` 一类错误；用 `--video`（或显式 `--enable_cameras`）让脚本按相机/录像路径初始化渲染管线，通常更稳。

## Headless 录像链路

性能调试不一定一开始就用 Go2 + cameras 这类高成本组合。可以先用 CartPole 验证 `--video` 离屏渲染链路：

```text
--num_envs 64 --max_iterations 1 --video --video_length 40 --video_interval 1
```

预期输出应包含录像目录、视频长度和至少一轮训练：

```text
[INFO] Recording videos during training.
video_folder: .../logs/rsl_rl/cartpole/<run_folder>/videos/train
Learning iteration 0/1
Training time: 1.33 seconds
```

如果无相机 headless 能训练、加视频后失败，优先查渲染 extension、驱动和显示环境；如果加视频后显存明显上升，先降低 `--num_envs`、视频长度和相机数量，再回到大任务。

## 小结

- 先查任务闭环，再查算法超参。
- reward 不涨时优先检查 observation、action、reward、termination。
- 吞吐低要区分 GPU、CPU、显存和渲染瓶颈。
- 视频和可视化标记是发现坐标系、目标采样和 reward hacking 的关键工具。

## 导航

- 上一页：[多 GPU 与分布式](06-distributed.md)
- 返回目录：[训练与评测](../05-training.md)
