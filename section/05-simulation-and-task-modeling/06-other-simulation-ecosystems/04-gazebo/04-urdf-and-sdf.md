# 机器人模型描述：URDF 与 SDF

目标：分清 URDF 和 SDF 的用途，知道机器人模型为什么不能只看外观，还要检查 link、joint、collision、inertial、sensor 和 plugin。

Gazebo 初学者经常会卡在一个问题上：机器人模型到底应该写 URDF，还是写 SDF？如果你只看文件后缀，很容易觉得它们只是两种 XML 格式。但在机器人系统里，它们的出发点不一样。

URDF 更常见于 ROS 机器人描述。它擅长描述一个机器人本体的 link 和 joint 关系，配合 `robot_state_publisher`、RViz、TF、MoveIt 等 ROS 工具使用。SDF 更常见于仿真世界描述。它不仅能描述机器人，还能描述 world、光源、物理参数、传感器、插件、嵌套模型和更完整的仿真环境。Gazebo 原生使用 SDF / SDFormat。

## URDF 适合描述什么

URDF 可以理解成“机器人身体结构说明书”。它通常关心：

| 内容 | 例子 | 作用 |
|---|---|---|
| link | `base_link`、`wheel_left_link`、`camera_link` | 机器人刚体部件 |
| joint | `left_wheel_joint`、`camera_joint` | 部件之间怎么连接 |
| visual | mesh、box、cylinder | RViz 和 Gazebo 中看得到的外观 |
| collision | 简化几何体或 mesh | 碰撞检测和物理接触 |
| inertial | mass、inertia、origin | 动力学计算需要的质量和惯量 |

ROS 项目里常会用 `.xacro` 生成 URDF。这样可以用变量、宏和参数组织复杂模型，比如左右轮重复结构、传感器安装位置、不同机器人版本的尺寸差异等。

但是 URDF 本身不擅长描述完整仿真世界。比如一个房间、多个模型、光照、物理引擎配置、Gazebo 系统插件，这些更适合放在 SDF world 中。

## SDF 适合描述什么

SDF 可以理解成“仿真世界说明书”。一个 SDF 文件可以描述完整 world，也可以描述单个 model。它可以包含：

```xml
<sdf version="1.9">
  <world name="demo_world">
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <model name="mobile_robot">
      <!-- links, joints, sensors, plugins -->
    </model>
  </world>
</sdf>
```

在 Gazebo 中，SDF 的优势是它天然知道“这是一个仿真场景”。你可以在同一个 world 里放机器人、障碍物、地面、灯光、传感器系统和控制插件。比如差速驱动插件、传感器系统、场景广播系统，通常都通过 SDF 中的 `<plugin>` 标签加载。

## 两者不是二选一

实际项目里经常会出现三种做法：

| 做法 | 常见场景 | 注意点 |
|---|---|---|
| URDF / xacro 为主，Gazebo 里补插件 | 传统 ROS 机器人项目 | 要确认 Gazebo 版本和插件写法是否匹配 |
| SDF world + SDF model 为主 | 新版 Gazebo 教程、纯仿真项目 | ROS 侧如果需要 TF 和模型显示，要处理好描述来源 |
| URDF 和 SDF 同时维护 | 复杂项目或历史项目 | 最容易出现两个模型不一致，需要严格同步 |

新版 Gazebo 和 ROS 2 的部分工作流正在减少“双份模型”的负担，例如用 SDFormat 相关解析能力让同一份描述服务 Gazebo 和 ROS。但这并不代表所有项目都已经可以无痛切换。

## 模型检查重点

一个能正常显示的模型，不等于能正常仿真。检查模型时建议按下面顺序看：

1. 坐标系：`base_link`、传感器 frame、轮子 frame 的方向是否合理。
2. 关节：关节类型、父子 link、轴方向、限制范围是否正确。
3. collision：碰撞体是否存在，是否过复杂，是否和 visual 严重不一致。
4. inertial：质量和惯量是否合理，是否出现 0 质量或离谱惯量。
5. 传感器：传感器挂在哪个 link 上，topic、频率、视场、量程是否正确。
6. 插件：插件文件名、插件类型、joint 名称、topic 名称是否和模型一致。

最常见的问题不是 XML 语法错，而是“名字对不上”。比如 DiffDrive 插件里写了 `left_wheel_joint`，模型里真正的 joint 叫 `left_wheel_joint_1`；或者 ROS bridge 订阅 `/cmd_vel`，Gazebo 插件实际听的是 `/model/robot/cmd_vel`。这些都不会靠肉眼看模型外观发现。

## 进一步阅读可以看：

- [SDF worlds](https://gazebosim.org/docs/latest/sdf_worlds/)
- [Spawn URDF](https://gazebosim.org/docs/latest/spawn_urdf/)
- [ROS 2 interoperability](https://gazebosim.org/docs/latest/ros2_interop/)