"""打印一个机器人的 joint / body 结构（Isaac Lab 5.x）。

导入自定义机器人后第一件该做的事，不是写 reward，而是确认 USD 转得对不对、
关节和连杆到底叫什么名字、默认关节角和关节限位是多少。本脚本**不依赖任何
任务定义**：只 spawn 一个机器人、打印结构、空跑几步确认能稳定加载，然后退出。

内置 Franka / ANYmal / Cartpole 三个可直接试的机器人，也能用 `--usd` 指向
你自己转好的 USD。

运行（在装好 Isaac Lab 的机器上，仓库根目录执行）：

    # 内置机器人，直接可跑（先验证脚本本身）
    ./isaaclab.sh -p labs/06_isaac_lab/print_robot_names.py --robot franka --headless

    # 换成你自己转好的 USD
    ./isaaclab.sh -p labs/06_isaac_lab/print_robot_names.py --usd /path/to/your_robot.usd --headless

打印出的 joint names / body names，正是后面写 `ArticulationCfg.actuators
.joint_names_expr`、ActionCfg、关节观测、reward 里 body 距离时要一一对上的名字。
把控制台输出贴进文档即可。
"""

import argparse

from isaaclab.app import AppLauncher

# 内置机器人预设 -> isaaclab_assets 里的 cfg 名
PRESETS = {
    "cartpole": "CARTPOLE_CFG",
    "franka": "FRANKA_PANDA_CFG",
    "anymal": "ANYMAL_C_CFG",
}

parser = argparse.ArgumentParser(description="打印机器人 joint / body 结构。")
parser.add_argument("--robot", choices=list(PRESETS), default="franka", help="内置机器人预设。")
parser.add_argument("--usd", type=str, default=None, help="自定义 USD 路径（给定时优先于 --robot）。")
parser.add_argument("--steps", type=int, default=60, help="打印后空跑步数，确认能稳定加载。")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# 先启动 Omniverse App，之后才能 import isaaclab 的其余模块
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.sim import SimulationContext


def build_robot_cfg() -> ArticulationCfg:
    """根据 --usd / --robot 构造 ArticulationCfg，prim 固定在 /World/Robot。"""
    if args_cli.usd:
        # 自定义机器人：给所有关节配一个隐式 actuator，增益用 None 表示沿用 USD drive。
        # 只为读结构，不需要精确的 stiffness/damping。
        return ArticulationCfg(
            prim_path="/World/Robot",
            spawn=sim_utils.UsdFileCfg(usd_path=args_cli.usd),
            actuators={
                "all": ImplicitActuatorCfg(joint_names_expr=[".*"], stiffness=None, damping=None),
            },
        )
    # 内置机器人：直接复用官方 cfg，只把 prim_path 换成单机器人路径
    import isaaclab_assets

    base = getattr(isaaclab_assets, PRESETS[args_cli.robot])
    return base.replace(prim_path="/World/Robot")


def _joint_limits(robot: Articulation):
    """跨版本取关节位置限位 (num_joints, 2)；取不到返回 None。"""
    for attr in ("joint_pos_limits", "soft_joint_pos_limits", "default_joint_pos_limits"):
        tensor = getattr(robot.data, attr, None)
        if tensor is not None:
            return tensor[0].tolist()
    return None


def dump_structure(robot: Articulation) -> None:
    print("=" * 76)
    print(f"prim_path  : {robot.cfg.prim_path}")
    print(f"num_joints : {robot.num_joints}")
    print(f"num_bodies : {robot.num_bodies}")
    try:
        print(f"fixed_base : {robot.is_fixed_base}")
    except Exception:  # 个别版本无此属性，忽略即可
        pass

    print("-" * 76)
    print("Joint names:", robot.data.joint_names)
    print("Body names :", robot.data.body_names)

    print("-" * 76)
    default_q = robot.data.default_joint_pos[0].tolist()
    limits = _joint_limits(robot)
    header = f"{'joint':<30}{'default':>10}{'lower':>10}{'upper':>10}"
    print(header)
    for i, name in enumerate(robot.data.joint_names):
        if limits is not None:
            lo, hi = limits[i]
            print(f"{name:<30}{default_q[i]:>10.3f}{lo:>10.3f}{hi:>10.3f}")
        else:
            print(f"{name:<30}{default_q[i]:>10.3f}")
    print("=" * 76)


def main() -> None:
    sim = SimulationContext(sim_utils.SimulationCfg(dt=0.005, device=args_cli.device))
    sim.set_camera_view(eye=(2.5, 2.5, 1.8), target=(0.0, 0.0, 0.5))

    # 地面 + 灯光（不依赖 prim_utils，直接用 spawn cfg 的 func 建 prim）
    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func("/World/defaultGroundPlane", ground_cfg)
    light_cfg = sim_utils.DomeLightCfg(intensity=3000.0)
    light_cfg.func("/World/Light", light_cfg)

    robot = Articulation(build_robot_cfg())

    # 必须先 reset，关节/连杆名和默认状态才会被填好
    sim.reset()
    print("[INFO] scene ready, dumping robot structure ...")
    dump_structure(robot)

    # 空跑几步：维持默认关节角，确认机器人能稳定加载（不会立刻炸/穿地）
    sim_dt = sim.get_physics_dt()
    for _ in range(args_cli.steps):
        if not simulation_app.is_running():
            break
        robot.set_joint_position_target(robot.data.default_joint_pos)
        robot.write_data_to_sim()
        sim.step()
        robot.update(sim_dt)


if __name__ == "__main__":
    main()
    simulation_app.close(wait_for_replicator=False, skip_cleanup=True)
