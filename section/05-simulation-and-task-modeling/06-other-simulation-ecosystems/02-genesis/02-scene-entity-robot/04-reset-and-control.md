# reset 与 control

本页专门区分直接设置状态和通过控制器发命令。`set_*` 更适合 reset 或调试初始状态，`control_*` 才表达执行过程。

## 本节目标

本节围绕下面几个问题展开：

1. `set_dofs_position()` 为什么更像 reset，而不是控制？
2. `control_dofs_position()` 为什么需要后续 `scene.step()` 才能体现效果？
3. episode reset、动作执行和状态观测应该怎样分开？
4. 初学时如何判断脚本是在控制机器人，而不是只把状态写过去？

## set 和 control 的区别

可以先用一句话区分：

| 方法 | 更像什么 | 用途 |
|---|---|---|
| `set_*` | 直接改状态 | reset、初始化、调试 |
| `control_*` | 发送控制目标 | 执行动作、模拟控制过程 |

如果用 `set_dofs_position()` 把机器人放到某个关节角，那更像把状态写过去。真正的控制应该是发目标，然后让物理循环推进。下面片段默认已经创建好 `scene`，`franka` 是场景里的机器人实体，并且 `dofs_idx` 已按上一页的关节名核对完成：

```python
target_qpos = [0, 0, 0, -1.0, 0, 1.0, 0, 0.04, 0.04]
franka.control_dofs_position(target_qpos, dofs_idx)
for _ in range(100):
    scene.step()
```

没有后续 `scene.step()`，控制目标不会变成一段可观察的运动过程。

官方 `sim_00_control_your_robot` 很适合拿来对照这一点。canonical run 的 `runs/genesis_readme_showcase_canonical_20260608_055500/summaries/sim_00_control_your_robot.json` 里，它是 `175` 帧、`1060x580`、`result: passed`，说明官方控制示例可以被无界面相机捕获到可见运动；但该记录是 bounded capture，不等同于完整运行全过程。视频只能说明“运动过程可见”，不能单独说明脚本是否区分了 reset 和 control。配套脚本 `03_robot_and_control.py` 额外保存 `reset_q`、`target_q` 和 `control_steps`，用于补上这层语义。

## episode 里三件事分开

机器人任务通常有三个阶段：

| 阶段 | 典型操作 |
|---|---|
| reset | `set_*` 设置初始状态，清空历史 |
| action | `control_*` 发送目标或力矩 |
| observe | 读取关节、位姿、相机或传感器 |

把这三件事混在一起，会让训练和调试很痛苦。比如每一步都用 `set_*`，机器人看起来“动了”，但那不是控制器在物理世界中执行动作。

## 验收标准

配套脚本 `03_robot_and_control.py` 的目标不是做任务，而是验证：

1. 能加载 Franka；
2. 能找到 dof 数量和关节索引；
3. reset 后状态符合预期；
4. 发出位置控制后，连续 step 能改变状态；
5. 摘要 JSON 记录目标和结果。

如果控制无效，先查 dof 维度和目标 shape，再查是否真的执行了 `scene.step()`。

摘要里应该能看到这几类字段：

```json
{
  "joint_names": ["joint1", "...", "finger_joint2"],
  "dofs_idx": [0, 1, 2, 3, 4, 5, 6, 7, 8],
  "reset_q": [0, 0, 0, -1.0, 0, 1.0, 0, 0.04, 0.04],
  "target_q": [0.3, 0.2, 0.0, -1.2, 0.0, 1.2, 0.2, 0.02, 0.02],
  "control_steps": 300,
  "result": "passed"
}
```

这里最值得检查的是 `reset_q` 和 `target_q` 不一样。前者是起点，后者是控制目标。如果只保存一个姿态数组，就很难判断脚本到底是 reset 了机器人，还是发出了真正的控制命令。

## 从官方视频回到结构化证据

读 `sim_00_control_your_robot` 时，可以按这个顺序检查：

| 证据 | 作用 |
|---|---|
| 官方预览 / 视频 | 确认控制示例产生了可见运动 |
| canonical run 的 `summaries/sim_00_control_your_robot.json` | 确认帧数、分辨率、运行耗时和 `result` |
| `03_robot_and_control.json` | 确认 dof 索引、reset 姿态、控制目标和 step 数 |

这三层证据合起来，才算把“机器人动了”写成“机器人被正确控制”。如果只放视频，很容易把直接写状态、viewer 运动和控制器执行混成一件事。

## 读完应能回答

1. 为什么 `set_dofs_position()` 可以用于 reset，但不能直接当作策略动作？
2. `sim_00_control_your_robot` 的视频证明了什么，又没有证明什么？
3. 如果 `reset_q` 和 `target_q` 完全一样，这个控制脚本还剩下什么学习价值？

## 小结

- `set_*` 用于 reset 和调试，`control_*` 用于动作执行。
- 控制命令必须配合后续 step 才能体现。
- 任务代码要把 reset、action、observe 三个阶段分开，并用结构化摘要证明区别。

## 导航

- 上一页：[关节、自由度与控制](03-joint-dof-control.md)
- 返回目录：[场景、实体与机器人](../02-scene-entity-robot.md)
- 下一页：[观察、渲染与传感器](../03-observation-rendering-sensors.md)
