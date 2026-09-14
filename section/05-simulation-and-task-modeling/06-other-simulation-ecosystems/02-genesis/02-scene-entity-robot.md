# 场景、实体与机器人

跑通最小场景以后，下一步不是直接训练策略，而是把 Genesis 的场景和机器人链路拆开：世界如何组织，实体如何加入，机器人资产如何加载，关节目标如何发出。

这一组要把 Genesis 从“能 step”推进到“能控制机器人”。正式的观察、渲染和传感器验收会放到下一组单独讲；本组只保留 viewer / camera 作为调试边界的提示，避免读者把“看见机器人”直接写成“控制链路已验收”。

## 本节目标

本节围绕下面几个问题展开：

1. 机器人在 Genesis 里为什么也是 `Entity`？
2. 控制前为什么要先核对关节名和 dof 索引？
3. `set_*` 和 `control_*` 为什么不能混为一谈？
4. viewer 可以怎样辅助调试，又为什么不能替代结构化控制证据？
5. 控制脚本应该保存哪些结果，才能算真正跑通？

## 从“世界能跑”到“机器人能动”

第一次仿真只说明场景能构建、物理能推进。机器人控制还多了几层问题：

| 层 | 读者要确认什么 |
|---|---|
| 资产 | Franka 是否成功作为 `Entity` 加入场景 |
| 关节 | 关节名和 dof 索引是否对得上 |
| 初始状态 | reset 姿态是否稳定，机器人是否穿地或自碰撞 |
| 控制命令 | 目标位置、速度或力是否发给了正确 dof |
| 物理响应 | 命令发出后是否经过 `scene.step()` 才逐步体现 |

这里最容易犯的错，是把 `set_dofs_position()` 当成控制。它确实能让机器人姿态改变，但那更像 reset 或直接写状态；真正的控制要发目标，再通过后续 step 让物理和控制器产生结果。

这一点和 MuJoCo 里的学习问题相通：直接改 `qpos` 和通过 actuator 发控制不是一回事。这个区别如果没有说明清楚，很容易误以为“能摆姿态”就是“会控制机器人”。

## 观察先作为调试边界

机器人动起来以后，当然需要观察结果。但本组先只建立一条边界：viewer 适合人看，结构化摘要才适合验收控制链路。正式的 camera、sensor、图像保存和渲染排错，会在下一组展开。

| 路径 | 面向谁 | 典型用途 |
|---|---|---|
| viewer | 人 | 看机器人姿态、接触、穿模、运动方向 |
| 结构化摘要 | 程序 / 报告 | 保存 dof、reset 姿态、控制目标和 step 数 |

viewer 很适合调试，但它依赖图形环境，也不能自动说明 dof 索引、目标向量和 reset / control 的区别。控制章的正式证据应先落在：

```text
runs/genesis_codecheck_.../
  summaries/
    03_robot_and_control.json
```

只看窗口会丢掉很多信息；保存 dof、目标和 step，才方便复查机器人到底是被控制器推动，还是被直接写了状态。

## 配套脚本怎么用

这一组的核心脚本是：

```bash
python labs/06_genesis/03_robot_and_control.py
```

如果从统一入口运行，`run_all.sh` 会把它和下一组的相机脚本写入同一个 `runs/genesis_codecheck_*` 目录。第一次建议仍然关闭 viewer：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 bash labs/06_genesis/run_all.sh
```

等无界面控制通过后，再按需打开 viewer：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=1 python labs/06_genesis/03_robot_and_control.py
```

这个顺序很重要。先用日志和文件证明链路通，再用 viewer 辅助理解运动。不要把 viewer 当成唯一验收。

控制脚本的摘要字段要能证明“机器人命令链路通”：

| 摘要文件 | 关键字段 | 说明 |
|---|---|---|
| `03_robot_and_control.json` | `joint_names`、`dofs_idx` | 证明控制目标对应真实 dof |
| `03_robot_and_control.json` | `reset_q`、`target_q`、`control_steps` | 区分 reset 姿态和控制目标 |

如果这些字段缺失，就算 viewer 里看见机器人动了，也不算完成本组验收。相机 RGB、depth、sensor 输出和图像有效性放到下一组专门验收。

## 两个检查点

学习这一组时，最重要的是控制检查点：

| 检查 | 通过标准 |
|---|---|
| dof 索引 | 能打印 Franka 的 9 个 dof |
| reset | 能把机器人放到稳定初始姿态 |
| control | 发位置目标后，step 循环中机器人逐步响应 |
| 参数 | 能说明 `kp`、`kv`、`force_range` 大致影响什么 |

这个检查点通过后，才适合进入下一组，把 camera RGB、depth、sensor 输出、图像有效性和渲染日志单独验收。

## 学习顺序

这一组围绕“机器人能动、程序能看”展开：

| 页面 | 重点 |
|---|---|
| [Scene 与 Entity](02-scene-entity-robot/01-scene-entity.md) | 场景和实体的基本组织方式 |
| [机器人资产加载](02-scene-entity-robot/02-robot-assets.md) | MJCF / URDF / mesh 入口和官方 Franka |
| [关节、自由度与控制](02-scene-entity-robot/03-joint-dof-control.md) | dof 索引、位置控制、增益和力限制 |
| [reset 与 control](02-scene-entity-robot/04-reset-and-control.md) | 直接设置状态和控制器命令的边界 |

读这一组时要始终盯住一个区分：控制不是直接改状态，viewer 也不是控制证据。目标是先形成可复现的控制链路，再进入可保存的观测链路。

## 进入观察与渲染前

在进入下一组观察与渲染之前，先确认已经能解释下面这句话：

```text
单环境里，机器人控制目标是一条向量；程序观测要另存相机或传感器证据。
```

如果单环境里的 dof、控制目标和 reset / control 边界还没弄清楚，直接看 camera、sensor 或 `n_envs` 都会把简单问题放大。下一组会先处理 viewer、camera、sensor 和渲染验收；并行环境会再往后处理批量维度，多物理对象则继续后移。

## 读完应能回答

1. 一个资产能被相机拍到，为什么还不能说明它已经是可控机器人？
2. `reset_q` 和 `target_q` 分别应该证明什么？
3. 如果 viewer 里机器人动了，但 `03_robot_and_control.json` 没有 dof 和目标字段，报告结论应该怎样保守表述？

## 小结

- `Scene / Entity` 是实体对象进入 Genesis 物理世界的共同入口；camera / sensor 由 `Scene` 管理，但不等同于普通 `add_entity` 对象。
- 资产取景证明“能加载、能 build、能拍到”，控制摘要才证明“能按 dof 运动”。
- reset 是状态设置，control 是控制器命令，二者不能混写。
- 进入观察、并行和多物理之前，单机器人控制链路必须先有日志和 JSON 证据。

## 导航

- 上一页：[安装与环境检查](01-getting-started/04-install-and-env-check.md)
- 返回目录：[Genesis](../02-genesis.md)
- 下一页：[Scene 与 Entity](02-scene-entity-robot/01-scene-entity.md)
