# 附录：速查表

这一页不教新东西，把整个单元里最常用的 API、字段、代码片段集中放在一起，方便查阅。每一项都链接到首次详讲的页面。

## 常用 Python API

| API | 用途 | 详讲 |
|---|---|---|
| `mujoco.MjModel.from_xml_path(path)` | 从 MJCF 文件加载并编译模型 | [01-overview/03](01-overview/03-install-and-first-run.md) |
| `mujoco.MjModel.from_xml_string(xml)` | 从字符串加载模型 | [01-overview/03](01-overview/03-install-and-first-run.md) |
| `mujoco.MjData(model)` | 创建与模型对应的数据对象 | [01-overview/02](01-overview/02-mental-model.md) |
| `mujoco.mj_step(model, data)` | 推进一个仿真步 | [01-overview/02](01-overview/02-mental-model.md) |
| `mujoco.mj_forward(model, data)` | 刷新派生量（不推进时间） | [01-overview/02](01-overview/02-mental-model.md) |
| `mujoco.mj_resetDataKeyframe(m, d, i)` | 重置到第 i 个 keyframe | [02-modeling/08](02-modeling/08-keyframe-and-naming.md) |
| `mujoco.mj_name2id(m, type, name)` | 按名字查 ID（找不到返回 -1） | [02-modeling/08](02-modeling/08-keyframe-and-naming.md) |
| `mujoco.mj_id2name(m, type, id)` | 按 ID 查名字 | [02-modeling/08](02-modeling/08-keyframe-and-naming.md) |
| `mujoco.mj_jac(m, d, jacp, jacr, point, body)` | 计算雅可比矩阵 | [06-grasping/02](06-grasping-walkthrough/02-end-effector-control.md) |
| `mujoco.Renderer(model, h, w)` | 离屏渲染器 | [04-observation/04](04-observation-and-rendering/04-offscreen-renderer.md) |
| `renderer.update_scene(data)` | 同步状态到渲染场景 | [04-observation/04](04-observation-and-rendering/04-offscreen-renderer.md) |
| `renderer.render()` | 渲染一帧 RGB | [04-observation/04](04-observation-and-rendering/04-offscreen-renderer.md) |
| `mujoco.viewer.launch(m, d)` | 启动交互式 viewer（阻塞） | [04-observation/05](04-observation-and-rendering/05-interactive-viewer.md) |
| `mujoco.viewer.launch_passive(m, d)` | 启动被动 viewer（非阻塞） | [04-observation/05](04-observation-and-rendering/05-interactive-viewer.md) |
| `mujoco.mjx.put_model(model)` | CPU 模型转 MJX 格式 | [07-mjx/02](07-mjx-and-gpu/02-minimal-migration.md) |
| `mujoco.mjx.make_data(model)` | 创建 MJX 数据 | [07-mjx/02](07-mjx-and-gpu/02-minimal-migration.md) |
| `mujoco.mjx.step(model, data)` | MJX 推进一步（纯函数） | [07-mjx/02](07-mjx-and-gpu/02-minimal-migration.md) |

## mjModel 常用字段

| 字段 | 含义 | 示例值 (Panda) |
|---|---|---|
| `model.nq` | 位置坐标维度 | 9 |
| `model.nv` | 速度坐标维度 | 9 |
| `model.nu` | actuator（驱动）数量 | 8 |
| `model.nbody` | body 数量 | 12 |
| `model.njnt` | joint 数量 | 9 |
| `model.ngeom` | geom 数量 | 82（含地面的 scene.xml；panda.xml 本身 81） |
| `model.nsensor` | sensor 数量 | 0（Panda 默认无 sensor） |
| `model.ncam` | 模型定义的相机数量 | 0（Panda 未定义相机，自由相机不计入） |
| `model.opt.timestep` | 仿真步长 | 0.002 |
| `model.opt.gravity` | 重力加速度 | (0, 0, -9.81) |
| `model.body_mass` | 各 body 质量 | (nbody,) |
| `model.jnt_range` | 关节限位 | (njnt, 2) |
| `model.actuator_ctrlrange` | ctrl 范围 | (nu, 2) |

## mjData 常用字段

| 字段 | 含义 | 形状 |
|---|---|---|
| `data.qpos` | 关节位置 | (nq,) |
| `data.qvel` | 关节速度 | (nv,) |
| `data.ctrl` | 控制信号（用户写入） | (nu,) |
| `data.sensordata` | 传感器读数 | (nsensordata,) |
| `data.time` | 当前仿真时间 | 标量 |
| `data.ncon` | 当前接触点数量 | 标量 |
| `data.contact` | 接触信息数组 | (ncon,) |
| `data.body("X").xpos` | body X 的世界位置 | (3,) |
| `data.body("X").xquat` | body X 的世界朝向 | (4,) wxyz |
| `data.site("X").xpos` | site X 的世界位置 | (3,) |
| `data.joint("X").qpos` | joint X 的位置 | (1,) / (4,) / (7,)，视 joint 类型 |

## 代码片段：最小仿真循环

```python
import mujoco
model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)
for _ in range(100):
    data.ctrl[:] = compute_control(data)   # compute_control 换成自己的控制逻辑
    mujoco.mj_step(model, data)
    print(data.qpos[0])
```

## 代码片段：离屏渲染循环

```python
with mujoco.Renderer(model, height=480, width=640) as renderer:
    for _ in range(100):
        data.ctrl[:] = compute_control(data)
        mujoco.mj_step(model, data)
        renderer.update_scene(data)
        frame = renderer.render()
```

## 代码片段：抓取状态机骨架

```python
# 伪代码骨架：dist_to_target / close_gripper 等按任务自行实现，完整版见 06 抓取实战
phase = "REACH"
for step in range(800):
    if phase == "REACH":
        if dist_to_target() < 0.005:
            phase = "GRASP"
    elif phase == "GRASP":
        close_gripper()
        if gripper_closed() and data.ncon > 0:
            phase = "LIFT"
    elif phase == "LIFT":
        if lifted_enough():
            phase = "DONE"
    mujoco.mj_step(model, data)
```

## 代码片段：MJX 最小迁移

```python
import mujoco
import mujoco.mjx as mjx
import jax
model = mujoco.MjModel.from_xml_path("scene.xml")
mjx_model = mjx.put_model(model)
mjx_data = mjx.make_data(model)

@jax.jit
def step_fn(data, ctrl):
    data = data.replace(ctrl=ctrl)
    return mjx.step(mjx_model, data)
```

## 常用环境变量

| 变量 | 取值 | 作用 |
|---|---|---|
| `MUJOCO_GL` | `egl` / `osmesa` / `glfw` | 选择渲染后端 |
| `XLA_PYTHON_CLIENT_PREALLOCATE` | `false` | 禁止 JAX 预分配全部 GPU 显存 |

## 常见排错速查

| 现象 | 第一反应 |
|---|---|
| 渲染报错/黑图 | 设置 `MUJOCO_GL=egl`（或 `osmesa`） |
| 仿真发散/NaN | 减半步长 `model.opt.timestep` |
| 关节不跟踪目标 | 检查 `ctrlrange` 是否截断了目标值 |
| `sensordata` 为空 | `model.nsensor == 0`，模型没声明 sensor |
| 接触未发生 | 检查 collision geom 存在且 `contype ≠ 0` |
| 物体滑落 | 增大 `friction[0]`（两 geom 一起调，接触取 max）或夹紧力 |
| mj_step 后画面没变 | 忘了在 `render` 之前调 `update_scene` |
| `mj_name2id` 返回 -1 | 检查名字拼写和对象类型参数 |
| macOS `launch_passive` 卡住 | 用 `mjpython` 代替 `python` |

## 导航

- 上一节：[训练教程](08-training-recipes.md)
- 返回上级：[MuJoCo](../02-mujoco.md)
- 下一节：[Isaac Sim](../03-isaac-sim.md)
