# 调试与调参

仿真抓取失败往往有几种典型长相：方块直接弹飞、夹爪穿模、夹住了抬起来又滑落、末端卡在桌面上方动不了。认得出这些形态，看到一段失败回放时就大致知道该从哪里下手。

## 本节目标

本节把抓取调试整理成一套可查的工具，围绕几个问题：

1. 弹飞、穿模、滑落、振荡这几种失败各长什么样，该先怀疑哪个参数？
2. 多视角和接触可视化分别能帮上什么忙？
3. 调参该按什么顺序推进，才不会越调越乱？

## 常见失败形态

<figure class="doc-figure" aria-label="失败形态一览">
  <p class="doc-figure-title">四种最常见的抓取失败形态</p>
  <table>
    <tr><th>失败形态</th><th>直观描述</th><th>第一怀疑方向</th></tr>
    <tr><td>弹飞</td><td>方块被夹爪碰一下后高速飞出场景</td><td>夹紧力太大、闭合太快、或被压在桌面上产生巨大接触力</td></tr>
    <tr><td>穿模</td><td>夹爪手指直接穿过方块，好像方块不存在</td><td>collision geom 缺失或 contype=0</td></tr>
    <tr><td>滑落</td><td>夹住后抬起过程中方块从两指间滑出</td><td>friction 太小、夹紧力不够、方块太重</td></tr>
    <tr><td>振荡</td><td>末端在目标附近来回抖动，无法稳定到达</td><td>伺服增益太大、damping 太小、timestep 太大</td></tr>
  </table>
</figure>

## 失败 → 原因 → 参数对照表

| 失败现象 | 参数 1（最可能） | 参数 2 | 参数 3 |
|---|---|---|---|
| 方块弹飞 | 减小夹紧力（增大 ctrl[7]） | 减慢闭合速率 | 检查初始位置无重叠 |
| 夹爪穿模 | 确认 collision geom 存在 + contype≠0 | 检查 contype/conaffinity 是否按位配对 | 减小 timestep |
| 滑落 | 增大 friction[0]（方块与指尖一起调，接触取 max） | 增大夹紧力 | 减轻方块质量 |
| 振荡/抖动 | 减小伺服增益 | 增大 actuator damping | 减小 timestep |
| 末端动不了 | 检查是否碰到限位 | 减小目标步长 | 换 IK 初始猜测 |
| 仿真发散/NaN | 减小 timestep | 检查初始重叠 | 换更稳的 `implicit` 积分器（Panda 默认是 `implicitfast`） |

## 多视角观察法

调试抓取时，同时从三个视角观察通常很有助于定位问题：

| 视角 | 能看清什么 |
|---|---|
| 俯视 | 末端和方块在水平面内的对齐情况、方块是否到了目标位 |
| 侧面 | 末端高度、夹爪开合程度、方块是否被抬离桌面 |
| 机载（手腕相机） | 指尖和方块的接触细节、方块是否在两指正中间 |

推荐在 debug 循环里把三视角并排显示或保存为拼接图，这样任何一帧出问题时都能同时看到三个角度。

## 接触可视化定位

在 viewer 里开启接触可视化（`mjVIS_CONTACTPOINT` 和 `mjVIS_CONTACTFORCE`，夹爪闭合时不妨亲自开一次看看），能直观看到：

- **接触点在哪里**：确认接触发生在指尖和方块之间，而不是方块的边缘或桌面。
- **接触力多大、朝哪个方向**：力箭头朝向应该大致沿着两指连线方向（向内的夹持力）。如果出现很大的垂直力（向上或向下），说明指尖在下压方块，可能把方块压进桌面。
- **是否有不该有的接触**：比如方块底部和桌面一直在接触，这说明 lift 还没成功。

## 调参顺序：先稳后准

一个推荐的调参工作流：

1. **先让仿真不崩溃**（timestep、积分器、初始位姿无重叠）。用最简单的控制（关节空间、固定 ctrl）跑 200 步，确认没有 NaN 和弹飞。
2. **再让夹爪能碰到物体**（collision 几何、接触参数）。用 viewer 确认接触点出现。
3. **再让夹爪能夹住**（friction、夹紧力）。重点调 friction[0] 和 ctrl[7]。
4. **再让手臂能稳定移动**（伺服增益、damping）。调增益让运动平滑不振荡。
5. **最后优化速度**（减少步数、增大 timestep）。在稳定的前提下提速度。

<figure class="doc-figure" aria-label="调参优先级">
  <p class="doc-figure-title">调参优先级：先稳后准再快</p>
  <div class="figure-pipeline">
    <div class="figure-node tone-green">
      <strong>① 稳定</strong>
      <span>timestep、积分器、初始姿态</span>
    </div>
    <div class="figure-node tone-blue">
      <strong>② 接触</strong>
      <span>collision geom、contype/conaffinity</span>
    </div>
    <div class="figure-node tone-gold">
      <strong>③ 夹住</strong>
      <span>friction、夹紧力</span>
    </div>
    <div class="figure-node tone-rose">
      <strong>④ 平滑</strong>
      <span>伺服增益、damping</span>
    </div>
    <div class="figure-node tone-green">
      <strong>⑤ 提速</strong>
      <span>减少步数、增大 timestep</span>
    </div>
  </div>
</figure>

## 小结

- 抓取的四种典型失败：弹飞（力太大）、穿模（无 collision）、滑落（摩擦小）、振荡（增益大）。
- 多视角 + 接触可视化是调试抓取很顺手的一组工具。
- 调参原则：先稳后准再快。先确保仿真不崩，再调接触，再优化速度。

## 参考资料

- [MuJoCo Documentation: Programming（可视化与调试）](https://mujoco.readthedocs.io/en/stable/programming/index.html)
- [MuJoCo Documentation: Computation（contact / friction）](https://mujoco.readthedocs.io/en/stable/computation/index.html)

## 导航

- 上一节：[完整抓取流程](04-full-pick-pipeline.md)
- 返回上级：[抓取实战](../06-grasping-walkthrough.md)
- 下一节：[MJX 与 GPU 并行](../07-mjx-and-gpu.md)
