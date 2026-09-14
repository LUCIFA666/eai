# URDF ↔ MJCF

如果接触过 ROS，对 URDF 多半不陌生。MuJoCo 也能直接加载 URDF，但“能加载”不等于“能完整跑”：actuator、sensor、tendon 这些 URDF 里没有的概念，都得手动补上。

## 本节目标

本节围绕“把 URDF 用进 MuJoCo”回答几个问题：

1. URDF 和 MJCF 各自侧重什么，为什么 MJCF 能表达更多东西？
2. MuJoCo 直接加载 URDF，能用到什么程度、缺什么？
3. 从 URDF 到一份可用的 MJCF，有哪几条路、要手动补哪些？

## URDF 与 MJCF 的关系

URDF 和 MJCF 不是互相替代的关系，它们描述同一台机器人时的关注点不同：

<figure class="doc-figure figure-compare" aria-label="MJCF 与 URDF 的侧重">
  <p class="doc-figure-title">URDF 与 MJCF 各有侧重</p>
  <div class="compare-panels">
    <section class="compare-panel">
      <div class="compare-label">URDF</div>
      <p class="compare-kicker">机器人结构说明书</p>
      <ul>
        <li>link / joint / 惯量 / 视觉与碰撞网格</li>
        <li>在 ROS、TF、MoveIt 生态里通用</li>
        <li>通常不含 actuator / sensor / tendon</li>
        <li>用 <code>&lt;joint&gt;</code> 指定父子 link 的连接关系</li>
      </ul>
    </section>
    <section class="compare-panel">
      <div class="compare-label">MJCF</div>
      <p class="compare-kicker">MuJoCo 的仿真模型</p>
      <ul>
        <li>body 树 / joint / geom / default 继承</li>
        <li>actuator、sensor、tendon、接触参数、灯光、相机</li>
        <li>可 <code>&lt;include&gt;</code> 组合成完整场景</li>
        <li>body 嵌套形成层级，joint 增加自由度</li>
      </ul>
    </section>
  </div>
</figure>

最关键的一个思维差异：**在 URDF 里，joint 用来指定"这两个 link 以什么方式连在一起"；在 MJCF 里，body 嵌套已经表达了父子关系，joint 的作用是"在这对父子之间增加自由度"，默认没 joint 就是焊死的。**

## MuJoCo 加载 URDF 的能力与限制

MuJoCo 可以直接加载 URDF 文件：

```python
model = mujoco.MjModel.from_xml_path("robot.urdf")
```

但加载之后会发现几个差异：

1. **nu = 0**：URDF 里没有 `<actuator>`，所以编译出来没有驱动。想让机器人受控地动，需要手动在 MJCF 里补上 actuator 定义。
2. **没有 sensor**：同理，`nsensor = 0`。
3. **没有 default**：URDF 加载后属性大多是显式写出的，文件往往比等效的 MJCF 长不少。
4. **碰撞几何可能需要调整**：URDF 通常把 visual mesh 也用作 collision mesh，在 MuJoCo 里一般更推荐用简化形状做碰撞几何。

一个好习惯是：加载 URDF 后先打印 `model.nq`、`model.nv`、`model.nu`、`model.nsensor`，确认模型的规模和功能是否符合预期。

## 转换工具与流程

从 URDF 转到 MJCF 有几种路径：

**路径 1：直接用 MuJoCo 加载 URDF**

最简单。把 URDF 直接喂给 `from_xml_path`，MuJoCo 内部会把它转成 `mjSpec` 再编译。适合"先用用看"的场景。但因为没有 actuator / sensor，只能跑被动动力学（比如方块落地），没法做受控仿真。

**路径 2：MuJoCo 自带编译器的格式转换**

MuJoCo 源码里自带一个 `compile` 示例程序，可以把 URDF 转存为 MJCF：

```bash
# 需要编译 MuJoCo 源码中的 compile 示例
# URDF → MJCF 转换
./compile robot.urdf robot.xml
```

转换后的 MJCF 使用了规范格式（所有坐标都展开为局部的，所有 inertial 显式写出），结构上正确但比较冗长。它可以作为起点，再手动添加 actuator、sensor、default 等。

**路径 3：手动改写**

对复杂机器人，自动转换的结果往往需要手动调整和瘦身。"手动改写"并不是要求从头写，而是拿自动转换的结果，把常见的属性提成 `<default>`，补上 actuator 和 sensor，用 `<include>` 把场景拆干净。下一页的动手练习就是做这件事。

## 转换后的常见手动调整

| 调整项 | 为什么 | 怎么做 |
|---|---|---|
| 补 actuator | URDF 没有，机器人动不了 | 加 `<actuator>` 节，至少为每个 joint 加一个 motor 或 position actuator |
| 分离 visual / collision | URDF 通常不分，MuJoCo 一般建议分开 | 给 visual geom 加 `contype=0 conaffinity=0 group=2`，collision geom 用简化形状 |
| 提 `<default>` | 自动转换的文件很长 | 找重复属性（如所有 hinge joint 的 damping），提成 default |
| 调摩擦和接触参数 | URDF 很少包含这些 | 加 `friction`、`solref`、`solimp` 属性 |
| 补 keyframe | URDF 没有预设姿态 | 加 `<keyframe>` 节，至少定义一个 home 位姿 |
| 检查 collision 凸性 | URDF 的 mesh 可能非凸 | 用简化形状（box/capsule/cylinder）做碰撞几何 |

## 小结

- URDF 描述机器人结构，MJCF 描述完整的仿真模型。URDF 可以被 MuJoCo 加载，但缺 actuator / sensor / tendon。
- 加载 URDF 后 `nu` 通常是 0，说明机器人有结构但没驱动。
- 从 URDF 到完整可用的 MJCF 的流程一般是：加载 → 检查规模 → 补 actuator/sensor → 分离 visual/collision → 提 default → 加 keyframe。
- 如果接触过 ROS，可以把 MJCF 理解为"URDF + actuator/sensor + 场景"。

## 动手练习

找一份 URDF 文件（例如从 ROS 包里取一个机器人模型），用 `from_xml_path` 加载，打印它的 `nq`、`nv`、`nu`、`nsensor`。重点看 `nu` 和 `nsensor`：URDF 里没有 `<actuator>` 和 `<sensor>`，这两个值应当都是 0，意味着模型“有结构、能算被动动力学，但还动不了、也没有传感器”。再和同一台机器人的 MJCF 版本对比 `nu`（通常大于 0），就能直观看出 MJCF 比 URDF 多补了哪些东西。

## 参考资料

- [MuJoCo Documentation: Modeling（含 URDF extensions）](https://mujoco.readthedocs.io/en/stable/modeling.html)
- [MuJoCo Documentation: XML Reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html)

## 导航

- 上一节：[keyframe 与命名](08-keyframe-and-naming.md)
- 返回上级：[建模](../02-modeling.md)
- 下一节：[动手：改一个模型](10-hands-on-modify.md)
