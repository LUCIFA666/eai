# 自定义机器人资产

内置机器人足够覆盖入门练习，但真实项目通常会遇到自己的机械臂、夹爪、移动底盘、四足或飞行器。Isaac Lab 不直接把“一个 URDF 文件”当训练资产使用，而是先进入 Isaac Sim / USD 生态，再由 Isaac Lab 用统一的资产配置加载。

## 本节目标

本节围绕下面几个问题展开：

1. 把自己的机器人（URDF / MJCF）变成 Isaac Lab 资产，要经过哪几步转换？
2. 怎么为它写 `ArticulationCfg`，并确认 joint / body 名称对得上？
3. 固定基座还是浮动基座、导入后常见问题，分别怎么排查？

基本流程可以写成：

```text
URDF / MJCF / mesh
  -> 转换为 USD
  -> 检查物理属性、碰撞体、关节名、body 名
  -> 写 ArticulationCfg
  -> 放入 InteractiveSceneCfg
  -> 用 observation / action / reward 构成任务
```

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-quadcopter.png" alt="Crazyflie 四旋翼资产" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">无论是内置 Crazyflie，还是自己导入的机器人，进入 Isaac Lab 后都要落到统一的资产接口：`ArticulationCfg` 声明，`data` 读取状态，actuator 下发控制。</figcaption>
</figure>

## 支持哪些来源

| 来源格式 | 常见来源 | 进入 Isaac Lab 前要做什么 |
|---|---|---|
| URDF | ROS 机器人描述、机械臂、移动底盘、四足 | 转成 USD，检查惯性、碰撞、关节轴 |
| MJCF | MuJoCo 模型 | 转成 USD，检查关节和 actuator 表达 |
| OBJ / STL / FBX / glTF | 物体、道具、场景模型 | 转成 USD 或直接作为 mesh 资源使用 |

训练机器人本体时，重点是 URDF / MJCF -> USD -> `ArticulationCfg`。普通操作物体通常进入 `RigidObjectCfg`；如果任务依赖形变，再考虑 `DeformableObjectCfg`。

## 为什么要转成 USD

USD 是 Isaac Sim 的原生场景描述格式。Isaac Lab 的大规模并行、克隆、instanceable 资产和 Omniverse 工具链都建立在 USD 之上。

把机器人转成 USD 不是一个形式步骤，它会影响：

- link、joint、body 在 stage 中的结构；
- 碰撞体和视觉体是否正确；
- 质量、惯性、关节限位是否保留；
- 是否能 instanceable，从而支持大规模克隆；
- 后续 `joint_names_expr`、`body_name` 能否正确匹配。

因此，导入机器人不是“转完就能训”，而是“转完后先检查”。

## URDF 转 USD

命令行转换通常通过 Isaac Lab 启动器执行。

```bash
./isaaclab.sh -p scripts/tools/convert_urdf.py \
    path/to/robot.urdf \
    path/to/output/robot.usd \
    --merge-joints
```

固定机械臂通常需要固定基座：

```bash
./isaaclab.sh -p scripts/tools/convert_urdf.py \
    path/to/arm.urdf \
    path/to/output/arm.usd \
    --fix-base \
    --merge-joints
```

浮动基座机器人，例如四足、人形、无人机，不应加 `--fix-base`，否则机器人根部会被固定在世界里。

| 参数 | 含义 | 常见选择 |
|---|---|---|
| `--fix-base` | 固定根 link | 固定机械臂开启；四足、人形、飞行器关闭 |
| `--merge-joints` | 合并固定关节，减少结构复杂度 | 通常开启 |
| self collision 相关选项 | 开启自碰撞 | 灵巧手、复杂接触任务才谨慎开启 |
| joint stiffness / damping | 写入 USD drive 参数 | 若由 Isaac Lab actuator 控制，避免和 Lab 侧重复打架 |

具体选项会随 Isaac Lab 版本变化，实际转换时以本地脚本 `--help` 输出为准。

## MJCF 转 USD

从 MuJoCo 生态迁移模型时，也优先使用 Isaac Lab 自带的命令行转换脚本。格式应和 URDF 转换保持一致：

```bash
./isaaclab.sh -p scripts/tools/convert_mjcf.py \
    path/to/robot.xml \
    path/to/output/robot.usd
```

如果是固定基座模型，例如固定机械臂，可以加固定基座选项：

```bash
./isaaclab.sh -p scripts/tools/convert_mjcf.py \
    path/to/arm.xml \
    path/to/output/arm.usd \
    --fix-base
```

如果需要在自己的 Python 流程里自动转换，也可以直接调用 converter API：

```python
from isaaclab.sim.converters import MjcfConverter, MjcfConverterCfg

converter_cfg = MjcfConverterCfg(
    asset_path="path/to/robot.xml",
    usd_dir="path/to/output",
    usd_file_name="robot.usd",
    fix_base=False,
)
converter = MjcfConverter(converter_cfg)
usd_path = converter.usd_path
```

MJCF 模型的 joint、actuator、geom 表达和 URDF 不同，转换后尤其要检查关节轴、限位和碰撞体。

有些 MJCF 转换出的 USD 会带多个 `UsdPhysics.ArticulationRootAPI`。这不一定说明转换失败，但 Isaac Lab 的 `ArticulationCfg(prim_path=...)` 需要在该 prim 子树下只解析到一个 articulation root。遇到这种情况，先检查 root，再写出一个只保留目标 root 的修复副本。注意 `labs/06_isaac_lab/` 下的脚本在本课程仓库中，与 IsaacLab 仓库是两个目录，运行时需要给出课程仓库里脚本的实际路径：

```bash
./isaaclab.sh -p labs/06_isaac_lab/repair_usd_articulation_roots.py \
    --usd path/to/output/robot.usd \
    --output path/to/output/robot_single_root.usd \
    --keep-root /robot/base/base \
    --headless
```

修复后再用 `labs/06_isaac_lab/print_robot_names.py --usd path/to/output/robot_single_root.usd --headless` 验证能否作为一个 `Articulation` 加载。不要只看“USD 文件生成了”就进入训练。

## instanceable

Isaac Lab 常常一次克隆几百到几千个环境。如果每个环境都完整复制一份机器人网格，显存会很快爆掉。instanceable USD 的意义是让多个环境共享同一份网格和资产数据，只保留各自的位姿和物理状态。

| 资产结构 | 并行环境增多时的结果 |
|---|---|
| instanceable | 共享底层资产，适合大规模克隆 |
| non-instanceable | 每个环境复制一份，显存和 stage 复杂度快速上涨 |

导入后若需要大规模训练，应确认 USD 是 instanceable 结构。手动编辑 USD 时也要避免破坏 instanceable 资产关系。

## 写 ArticulationCfg

转换完成后，在 Isaac Lab 中像使用内置机器人一样引用 USD：

```python
from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
import isaaclab.sim as sim_utils

my_robot = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/MyRobot",
    spawn=sim_utils.UsdFileCfg(
        usd_path="path/to/output/robot.usd",
        activate_contact_sensors=True,
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.4),
        joint_pos={
            ".*_hip_joint": 0.0,
            ".*_thigh_joint": 0.8,
            ".*_calf_joint": -1.5,
        },
    ),
    actuators={
        "legs": ImplicitActuatorCfg(
            joint_names_expr=[".*"],
            stiffness=25.0,
            damping=0.5,
        ),
    },
)
```

最重要的是三件事：

- `prim_path` 带 `{ENV_REGEX_NS}`，否则并行环境无法各自拥有机器人；
- `init_state.pos` 的高度合理，避免穿地或悬空；
- `actuators.joint_names_expr` 能匹配真实关节名。

## 打印 joint names 和 body names

导入后不要直接写 reward。先打印结构：

```python
robot = scene["robot"]

print("Joint names:", robot.data.joint_names)
print("Body names:", robot.data.body_names)
print("Num joints:", robot.num_joints)
print("Num bodies:", robot.num_bodies)
print("Default joint pos:", robot.data.default_joint_pos)
```

这些名字会被后续多个地方引用：

| 名称 | 会在哪里用到 |
|---|---|
| joint name | `joint_names_expr`、ActionCfg、关节观测、关节 reset |
| body name | 末端执行器、接触传感器、奖励中的 body 距离 |
| root body | 浮动基座状态、速度、摔倒判断 |

如果名字没有确认清楚，后面出现“动作无效”“传感器没有读数”“reward 一直为零”时会很难排查。

### 一个独立可跑的小脚本

上面的片段假设你已经在某个 env / scene 里拿到了 `robot`。但真正导入一个新机器人时，任务往往还没写，你只想先确认 USD 转得对不对、关节和 body 叫什么。这时更方便的是一个**不依赖任何任务定义**的独立脚本：只 spawn 机器人、打印结构、空跑几步确认能稳定加载，然后退出。

课程仓库提供的 `labs/06_isaac_lab/print_robot_names.py` 内置了 Franka / ANYmal / Cartpole 三个可直接试的机器人，也能用 `--usd` 指向你自己转好的 USD。下面保留核心结构，实际运行以仓库脚本为准：

```python
"""labs/06_isaac_lab/print_robot_names.py：spawn 一个机器人并打印它的关节 / 连杆结构。"""
import argparse

from isaaclab.app import AppLauncher

PRESETS = {"cartpole": "CARTPOLE_CFG", "franka": "FRANKA_PANDA_CFG", "anymal": "ANYMAL_C_CFG"}

parser = argparse.ArgumentParser(description="打印机器人 joint / body 结构。")
parser.add_argument("--robot", choices=list(PRESETS), default="franka")
parser.add_argument("--usd", type=str, default=None, help="自定义 USD 路径（优先于 --robot）。")
parser.add_argument("--steps", type=int, default=60, help="打印后空跑步数，确认能稳定加载。")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# 先启动 App，之后才能 import isaaclab 其余模块
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.sim import SimulationContext


def build_robot_cfg() -> ArticulationCfg:
    if args_cli.usd:  # 自己的机器人：给所有关节配隐式 actuator，增益沿用 USD（None）
        return ArticulationCfg(
            prim_path="/World/Robot",
            spawn=sim_utils.UsdFileCfg(usd_path=args_cli.usd),
            actuators={"all": ImplicitActuatorCfg(joint_names_expr=[".*"], stiffness=None, damping=None)},
        )
    import isaaclab_assets

    return getattr(isaaclab_assets, PRESETS[args_cli.robot]).replace(prim_path="/World/Robot")


def main() -> None:
    sim = SimulationContext(sim_utils.SimulationCfg(dt=0.005, device=args_cli.device))
    sim.set_camera_view(eye=(2.5, 2.5, 1.8), target=(0.0, 0.0, 0.5))

    ground = sim_utils.GroundPlaneCfg()
    ground.func("/World/defaultGroundPlane", ground)
    light = sim_utils.DomeLightCfg(intensity=3000.0)
    light.func("/World/Light", light)
    robot = Articulation(build_robot_cfg())

    sim.reset()  # 必须先 reset，关节 / 连杆名和默认状态才会被填好
    print("Joint names:", robot.data.joint_names)
    print("Body names :", robot.data.body_names)
    print("Num joints :", robot.num_joints, "| Num bodies:", robot.num_bodies)
    print("Default joint pos:", robot.data.default_joint_pos[0].tolist())

    sim_dt = sim.get_physics_dt()
    for _ in range(args_cli.steps):
        robot.set_joint_position_target(robot.data.default_joint_pos)
        robot.write_data_to_sim()
        sim.step()
        robot.update(sim_dt)


if __name__ == "__main__":
    main()
    simulation_app.close(wait_for_replicator=False, skip_cleanup=True)
```

运行（在装好 Isaac Lab 的机器、仓库根目录执行）：

```bash
# 内置机器人，直接可跑（先验证脚本本身）
./isaaclab.sh -p labs/06_isaac_lab/print_robot_names.py --robot franka --headless

# 换成你自己转好的 USD
./isaaclab.sh -p labs/06_isaac_lab/print_robot_names.py --usd /path/to/your_robot.usd --headless
```

两个要点：一是**必须先 `sim.reset()` 再读 `robot.data.*`**，否则关节名和默认状态都还没初始化；二是自定义 USD 用 `ImplicitActuatorCfg(joint_names_expr=[".*"], stiffness=None, damping=None)` 给全关节挂一个“沿用 USD 增益”的执行器，只为把结构读出来，不必先纠结控制参数。打印出的名字，就是接下来写 `joint_names_expr`、ActionCfg、关节观测和 reward 里 body 距离时要一一对上的。

## 固定基座和浮动基座

机器人导入时要先判断根部是否应该固定：

| 机器人类型 | 根部设置 | 例子 |
|---|---|---|
| 固定机械臂 | `fix_base=True` | Franka、UR、桌面机械臂 |
| 四足 / 人形 | `fix_base=False` | Go2、ANYmal、H1 |
| 飞行器 | `fix_base=False` | Crazyflie、quadcopter |
| 夹爪作为机械臂末端 | 取决于装配方式 | 单独测试可固定，整机中随机械臂运动 |

如果四足误设成固定基座，它永远跑不起来；如果固定机械臂没有固定基座，它可能会因为重力掉下去。

## 常见问题排查

**机器人穿地或漂浮**

检查 `init_state.pos` 的 z 值，以及 USD 中 root link 的原点位置。四足的 z 通常接近站立高度，固定机械臂常常需要根据底座坐标设置。

**关节完全不动**

先打印 `robot.data.joint_names`，确认 `joint_names_expr` 是否匹配。再检查 action 配置是否指向同一个 asset name。

**机器人疯狂抖动**

检查三类问题：关节惯性是否异常、碰撞体是否互相穿插、`stiffness` / `damping` 是否过高。导入模型的质量和惯性来自源文件，质量错误会让控制非常不稳定。

**碰撞体和视觉体不一致**

在 Isaac Sim GUI 中查看 collision mesh。很多 URDF 的 collision 为简化几何体，视觉模型漂亮不代表碰撞模型正确。

**训练一开多环境就爆显存**

检查 USD 是否 instanceable，模型网格是否过重，是否把不需要克隆的全局资产放进了 `{ENV_REGEX_NS}`。

**接触传感器没有数据**

确认加载 USD 时是否启用了 `activate_contact_sensors=True`，以及传感器配置中的 body 名是否匹配真实 body。

## 最小资产导入闭环

一个自定义机器人真正接入 Isaac Lab，至少要走完下面闭环：

```text
1. 转换 USD
2. 在 Isaac Sim 中打开，检查视觉、碰撞、质量、关节限位
3. 写 ArticulationCfg，设置 prim_path、spawn、init_state、actuators
4. 放进 InteractiveSceneCfg
5. 启动一个小 num_envs 场景，打印 joint_names / body_names
6. 给一个固定 action 或关节目标，确认机器人能稳定运动
7. 再进入 observation / reward / termination 的任务定义
```

不要跳过第 5 和第 6 步。机器人还没稳定站住或稳定响应控制时，训练算法无法替导入问题收拾残局。

不要只把 `path/to/robot.urdf` 替换成文件路径就结束。导入链路至少要用一个很小的最小可用资产做闭环验收：转换 USD、加载成 `Articulation`、打印 joint / body 名称，再给一个固定动作确认响应稳定。

| 验收点 | 预期现象 | 排错提示 |
|---|---|---|
| URDF 转 USD | 能生成 USD，并能在 Isaac Lab 中加载为单个 `Articulation` | 若 joint 数量为 0，检查 URDF joint 类型、fixed joint 合并和根 link |
| 打印结构 | 能看到明确的 `joint_names` 和 `body_names` | 后续 action、sensor、reward 都依赖这些名字，不要靠猜索引 |
| MJCF 转 USD | GUI experience 或可用显示环境下 importer 能注册并生成 USD | 纯 headless 下若出现 `MJCFCreateImportConfig` 未注册，优先换 Isaac Sim experience 或使用 `xvfb-run` |
| USD root 审计 | 一个机器人资产只有一个 articulation root | MJCF 转换后可能出现多个 root；多 root 建议先修成单 root，再进入训练任务 |
| 加载修复后的 USD | `Articulation` 能正常初始化，并能读到关节数量和关节名 | 如果初始化失败，先回到 USD prim 层级和 articulation root，而不是直接改训练脚本 |

真正要带走的经验是：**MJCF 转换完成后建议做 USD root 审计；如果出现多个 articulation root，先把资产修成单 root，再进入训练任务。** 这样写不是为了增加步骤，而是为了把“资产导入错了”和“训练算法没学会”区分开。

## 小结

- 自定义机器人进入 Isaac Lab 的主线是 URDF / MJCF -> USD -> `ArticulationCfg` -> `InteractiveSceneCfg`。
- 固定机械臂通常固定基座；四足、人形、飞行器通常保持浮动基座。
- 大规模并行训练需要 instanceable USD，否则显存和 stage 复杂度会随环境数快速增长。
- 导入后第一件事是打印 joint names 和 body names，它们决定后续 action、sensor、reward 能否正确绑定。
- 先验证机器人能稳定加载和响应控制，再开始写完整任务。

## 参考资料

- Isaac Lab How-To: Importing a New Asset. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab How-To: Writing an Articulation Configuration. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab Tutorial: Adding a New Robot. `scripts/tutorials/01_assets/add_new_robot.py`

## 导航

- 上一页：[执行器模型](02-actuators.md)
- 返回目录：[场景与机器人资产](../03-scene-and-robot.md)
- 下一页：[任务逻辑配置](../04-task-logic.md)
