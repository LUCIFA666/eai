# 场景与机器人资产

上一部分已经把一个 Isaac Lab 任务拆分。接下来要把最底层的 scene 真正搭起来。没有 scene，就没有机器人状态；没有执行器，策略动作无法作用到关节；没有可复用的机器人导入流程，课程任务就只能停留在内置资产上。

## 本节目标

本节围绕下面几个问题展开：

1. 一个资产怎么进入 Isaac Lab 的 `InteractiveSceneCfg`，并在大量并行环境里稳定存在？
2. 场景配置、执行器模型和自定义机器人这三块分别解决什么问题？
3. 学完这一章，你能不能把自己的机器人可训练、可调试地放进场景？

这一部分只处理“物理舞台和机器人本体”，还不急着写 observation、reward 和 termination。那些任务规则会放到下一部分。这里的核心问题是：一个 USD / URDF / MJCF 资产怎样进入 Isaac Lab 的 `InteractiveSceneCfg`，并在许多并行环境里以稳定、可训练、可调试的方式存在。

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [场景与资产配置](03-scene-and-robot/01-scene-and-assets.md) | 一个 Isaac Lab 场景由哪些资产组成？为什么 `{ENV_REGEX_NS}` 是并行环境的关键？ | `ArticulationCfg`、`RigidObjectCfg`、`DeformableObjectCfg`、`InteractiveSceneCfg`、`num_envs`、`env_spacing`、克隆 |
| [执行器模型](03-scene-and-robot/02-actuators.md) | 策略输出为什么不能直接等于真实关节力矩？执行器配置到底控制什么？ | implicit / explicit actuator、PD、DCMotor、执行器分组、stiffness / damping |
| [自定义机器人资产](03-scene-and-robot/03-custom-robot.md) | 自己的 URDF / MJCF 如何进入 Isaac Lab，并变成可训练的 `Articulation`？ | URDF / MJCF -> USD、instanceable、关节名 / body 名调试、常见导入问题 |

## 本部分的边界

Scene 只回答“世界里有什么”和“这些东西如何被批量克隆”。它不负责告诉策略看什么、怎么打分、什么时候结束。一个常见误区是把所有任务逻辑都塞进 scene；这样会让场景和训练规则混在一起，后面很难改。

本部分完成后，应该能把一个最小机器人任务拆成下面的层次：

```text
资产层：robot / object / table / ground / sensor
场景层：InteractiveSceneCfg(num_envs, env_spacing, replicate_physics)
执行层：actuators 把 action target 变成关节控制
任务层：observation / action / reward / termination / event
训练层：runner、algorithm、policy、log、checkpoint
```

本部分只写前三层。下一部分再写任务层。

## 读完本部分后

完成这一部分后，应该能看懂 `ArticulationCfg`、`RigidObjectCfg`、`AssetBaseCfg` 和 `InteractiveSceneCfg` 的分工，知道 `{ENV_REGEX_NS}` 为什么是并行克隆的入口，也能判断一个自定义机器人导入失败时应该先查 USD、关节名、执行器还是 instanceable 设置。

## 导航

- 上一页：[任务结构与 Manager 系统](02-reading-a-task.md)
- 返回上级：[Isaac Lab](../04-isaac-lab.md)
- 下一页：[任务逻辑配置](04-task-logic.md)
