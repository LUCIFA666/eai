"""Run the Isaac Sim 4.5 Franka RMPflow target-following example."""

from __future__ import annotations

import argparse
import sys

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=600)
    parser.add_argument("--control-hz", type=float, default=60.0)
    parser.add_argument("--max-substep", type=float, default=0.00334)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.steps <= 0 or args.control_hz <= 0 or args.max_substep <= 0:
        print("steps, control-hz and max-substep must be positive", file=sys.stderr)
        return 2

    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        from isaacsim.core.api import World
        from isaacsim.core.prims import Articulation, XFormPrim
        from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats
        from isaacsim.core.utils.nucleus import get_assets_root_path
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.robot_motion.motion_generation import (
            ArticulationMotionPolicy,
            RmpFlow,
        )
        from isaacsim.robot_motion.motion_generation.interface_config_loader import (
            load_supported_motion_policy_config,
        )

        dt = 1.0 / args.control_hz
        world = World(
            stage_units_in_meters=1.0,
            physics_dt=dt,
            rendering_dt=dt,
        )
        world.scene.add_default_ground_plane()

        assets_root = get_assets_root_path()
        if assets_root is None:
            raise RuntimeError("Isaac Sim assets root is unavailable")

        robot_path = "/World/Franka"
        add_reference_to_stage(
            assets_root + "/Isaac/Robots/Franka/franka.usd", robot_path
        )
        robot = Articulation(robot_path)

        target_path = "/World/target"
        add_reference_to_stage(
            assets_root + "/Isaac/Props/UIElements/frame_prim.usd", target_path
        )
        target = XFormPrim(target_path, scale=np.array([0.04, 0.04, 0.04]))
        target_orientation = euler_angles_to_quats(np.array([0.0, np.pi, 0.0]))

        world.reset()
        robot.initialize()

        config = load_supported_motion_policy_config("Franka", "RMPflow")
        config["maximum_substep_size"] = args.max_substep
        rmpflow = RmpFlow(**config)
        articulation_policy = ArticulationMotionPolicy(robot, rmpflow)

        print("active joints:", rmpflow.get_active_joints())
        print("watched joints:", rmpflow.get_watched_joints())
        for frame in range(args.steps):
            t = frame * dt
            target_position = np.array([0.5, 0.12 * np.sin(0.6 * t), 0.7])
            target.set_world_pose(target_position, target_orientation)

            rmpflow.set_end_effector_target(target_position, target_orientation)
            action = articulation_policy.get_next_articulation_action(dt)
            robot.apply_action(action)
            world.step(render=not args.headless)

            if action.joint_positions is not None and not np.isfinite(
                action.joint_positions
            ).all():
                raise FloatingPointError(f"non-finite action at frame {frame}")

        print(f"[OK] completed {args.steps} steps at {args.control_hz:g} Hz")
        return 0
    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
