# 夹爪控制

末端到了方块上方，还剩三件事：闭合夹爪、确认真的夹住了、抬起时别让它滑掉。每一件都比表面看起来稍微复杂一点。

## 本节目标

本节围绕“稳稳夹住”回答几个问题：

1. Panda 夹爪的 actuator 怎么用 ctrl 控制开合？
2. 怎么从接触判断物体到底夹住了没？
3. 物体太滑、夹不住时，从哪些参数入手？

## 夹爪 actuator 怎么写 ctrl

回顾 [tendon 与 equality](../03-control-and-physics/03-tendon-and-equality.md)：Panda 的夹爪用 1 个 actuator（`actuator8`）通过 tendon 驱动两根手指。ctrl 的范围是 `[0, 255]`，0 对应闭合，255 对应完全张开。

```python
# 张开夹爪
data.ctrl[7] = 255   # actuator8 在 ctrl 数组的第 8 个位置（下标 7）
for _ in range(100):
    mujoco.mj_step(model, data)

# 闭合夹爪（用力夹）
data.ctrl[7] = 0
for _ in range(100):
    mujoco.mj_step(model, data)
```

这里的 ctrl 语义和臂关节其实一致，都是位置伺服：臂 actuator 的 ctrl 是目标角度，夹爪 actuator 的 ctrl 是目标开度，只是被线性重映射到了 `[0, 255]`（对应手指开度 0→0.04m）。`actuator8` 的 `biasprm` 里带了位置增益（kp=100），所以当手指被物体挡住、到不了目标开度时，位置误差就转化成了夹持力，这也是把 ctrl 往 0 调会“夹得更紧”的原因。

<figure class="doc-figure" aria-label="夹爪 ctrl 值对照">
  <p class="doc-figure-title">夹爪 ctrl 值对照</p>
  <table>
    <tr><th>ctrl[7] 值</th><th>效果</th><th>适用阶段</th></tr>
    <tr><td>255</td><td>完全张开（每根手指行程约 4cm）</td><td>reach（接近物体前）</td></tr>
    <tr><td>100-150</td><td>部分闭合（手指靠近物体）</td><td>预抓取</td></tr>
    <tr><td>0-50</td><td>用力闭合（最大夹持力）</td><td>grasp（抓住物体）</td></tr>
  </table>
</figure>

## 用接触力检测"夹住了没"

最简单的方法：读 `data.contact`，检查指尖和方块之间是否有接触：

```python
def is_grasped(data, model):
    """指尖（left_finger / right_finger）和方块之间是否有接触"""
    # Panda 的指尖碰撞 geom 没有单独命名，所以用它们所属的 body 来识别
    left = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "left_finger")
    right = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "right_finger")
    block_geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "block_geom")
    finger_bodies = {left, right}

    for i in range(data.ncon):
        c = data.contact[i]
        body1 = model.geom_bodyid[c.geom1]
        body2 = model.geom_bodyid[c.geom2]
        # 一个 geom 属于手指、另一个是方块
        if (body1 in finger_bodies and c.geom2 == block_geom) or \
           (body2 in finger_bodies and c.geom1 == block_geom):
            return True
    return False
```

更可靠的方法是用 `touch` sensor（见 [sensor 与 sensordata](../04-observation-and-rendering/02-sensors.md)），在 MJCF 里给指尖加 touch sensor，然后直接读 `data.sensor("left_touch").data`，非零就是有接触力。

## 防滑：调 friction 还是调 ctrl

如果物体总是滑落，通常可以按这个顺序试：

1. **加大夹紧力**：把 ctrl[7] 往 0 调（比如从 50 降到 0），夹持力更大。
2. **增大 friction**：把方块和指尖 collision geom 的 `friction[0]` 从默认的 1.0 增大到 2.0-3.0。
3. **检查 collision 几何**：确认指尖的 collision geom 尺寸合理，别太小。

需要特别提醒：MuJoCo 把接触摩擦取成**两个接触 geom 的较大值**（element-wise max）。Panda 指尖 pad 默认 `friction[0]=1.0`，所以**只调方块、不调指尖往往看不出变化**（`max(0.3, 1.0)` 还是 1.0）。下表里的 `friction[0]` 指的是接触有效摩擦，要看到差异得把方块和指尖一起调低。

<figure class="doc-figure" aria-label="防滑调参表">
  <p class="doc-figure-title">防滑调参对照表</p>
  <table>
    <tr><th>ctrl[7]</th><th>friction[0]</th><th>方块质量</th><th>结果</th></tr>
    <tr><td>50</td><td>1.0</td><td>0.05</td><td>可能夹不住（力不够）</td></tr>
    <tr><td>0</td><td>1.0</td><td>0.05</td><td>通常可以夹住</td></tr>
    <tr><td>0</td><td>0.3</td><td>0.05</td><td>容易滑落（摩擦太小）</td></tr>
    <tr><td>0</td><td>3.0</td><td>0.05</td><td>稳定夹住</td></tr>
    <tr><td>0</td><td>1.0</td><td>0.2</td><td>可能夹不住（太重）</td></tr>
  </table>
</figure>

## 闭环抓取：力反馈调整夹紧度

"开环抓取"指设一个固定 ctrl 就不再管了，遇到摩擦力、物体质量变化时往往容易失败。"闭环抓取"则根据接触力反馈，动态调整夹紧程度：

```python
def closed_loop_grasp(model, data, target_force=2.0, steps=200):
    """闭环抓取：根据指尖接触力反馈动态调夹紧力"""
    left = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "left_finger")
    right = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "right_finger")
    block = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "block_geom")
    f6 = np.zeros(6)
    for _ in range(steps):
        mujoco.mj_step(model, data)

        # 累加指尖和方块之间所有接触的法向力
        grip_force = 0.0
        for i in range(data.ncon):
            c = data.contact[i]
            b1, b2 = model.geom_bodyid[c.geom1], model.geom_bodyid[c.geom2]
            on_block = block in (c.geom1, c.geom2)
            on_finger = b1 in (left, right) or b2 in (left, right)
            if on_block and on_finger:
                mujoco.mj_contactForce(model, data, i, f6)
                grip_force += abs(f6[0])   # f6[0] 是接触法向力

        # 力不够 → 夹更紧；力太大 → 松一点（防止损坏物体或弹飞）
        if grip_force < target_force:
            data.ctrl[7] = max(data.ctrl[7] - 2, 0)
        elif grip_force > target_force * 1.5:
            data.ctrl[7] = min(data.ctrl[7] + 1, 255)
```

闭环抓取比开环更鲁棒。接触法向力可以用 `mj_contactForce` 直接从接触约束里读出来（上面的 `f6[0]` 就是），不一定要额外加 touch sensor。

## 失败案例

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 手指穿过了方块 | collision geom 丢失或 contype=0 | 检查指尖 collision geom 存在且 contype≠0 |
| 夹住但抬起来时方块滑落 | friction 不够，或夹紧力不够 | 增大 friction[0] 或减小 ctrl[7] |
| 方块被弹飞 | 夹紧力太大，或 gripper 闭合太快 | 减小 ctrl 变化速率，给更多步让手指慢慢闭合 |
| 只夹到方块边缘 | 末端定位不准，方块不在两指正中间 | 调整 reach 阶段的目标位姿 |

## 小结

- Panda 夹爪用 1 个 actuator（ctrl[7]）控制 2 根手指，`[0, 255]` 对应从闭合到张开的目标开度（位置伺服，被物体挡住时产生夹持力）。
- 用 `data.contact` 或 touch sensor 判断物体是否被夹住。
- 防滑优先增大夹紧力和 friction，先确认 collision 几何正确。
- 闭环抓取比开环鲁棒，接触力可以用 `mj_contactForce` 直接读出来。

## 参考资料

- [MuJoCo Documentation: Computation（contact force）](https://mujoco.readthedocs.io/en/stable/computation/index.html)
- [MuJoCo Documentation: Modeling — Contact parameters（两 geom 摩擦取 element-wise max 的规则）](https://mujoco.readthedocs.io/en/stable/modeling.html#contact-parameters)
- [MuJoCo Documentation: Python Bindings（mj_contactForce）](https://mujoco.readthedocs.io/en/stable/python.html)
- [MuJoCo Menagerie: Franka Emika Panda](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda)

## 导航

- 上一节：[末端控制](02-end-effector-control.md)
- 返回上级：[抓取实战](../06-grasping-walkthrough.md)
- 下一节：[完整抓取流程](04-full-pick-pipeline.md)
