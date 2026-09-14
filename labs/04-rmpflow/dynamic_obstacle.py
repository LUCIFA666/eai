"""Franka RMPflow example with a moving cuboid and world-state updates."""

from __future__ import annotations

import argparse
import sys

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=900)
    parser.add_argument("--control-hz", type=float, default=60.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.steps <= 0 or args.control_hz <= 0:
        return 2
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import FixedCuboid
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
        world = World(stage_units_in_meters=1.0, physics_dt=dt, rendering_dt=dt)
        world.scene.add_default_ground_plane()
        assets_root = get_assets_root_path()
        if assets_root is None:
            raise RuntimeError("Isaac Sim assets root is unavailable")

        add_reference_to_stage(
            assets_root + "/Isaac/Robots/Franka/franka.usd", "/World/Franka"
        )
        robot = Articulation("/World/Franka")
        add_reference_to_stage(
            assets_root + "/Isaac/Props/UIElements/frame_prim.usd", "/World/target"
        )
        target = XFormPrim("/World/target", scale=np.array([0.04] * 3))
        obstacle = world.scene.add(
            FixedCuboid(
                prim_path="/World/obstacle",
                name="obstacle",
                position=np.array([0.42, 0.0, 0.62]),
                size=0.08,
                color=np.array([0.0, 0.2, 1.0]),
            )
        )
        orientation = euler_angles_to_quats(np.array([0.0, np.pi, 0.0]))

        world.reset()
        robot.initialize()
        config = load_supported_motion_policy_config("Franka", "RMPflow")
        rmpflow = RmpFlow(**config)
        if rmpflow.add_obstacle(obstacle) is False:
            raise RuntimeError("RMPflow rejected the cuboid obstacle")
        articulation_policy = ArticulationMotionPolicy(robot, rmpflow)

        for frame in range(args.steps):
            t = frame * dt
            target_position = np.array([0.55, 0.0, 0.68])
            obstacle_position = np.array([0.42, 0.18 * np.sin(0.8 * t), 0.62])
            target.set_world_pose(target_position, orientation)
            obstacle.set_world_pose(position=obstacle_position)

            rmpflow.set_end_effector_target(target_position, orientation)
            rmpflow.update_world()
            base_position, base_orientation = robot.get_world_pose()
            rmpflow.set_robot_base_pose(base_position, base_orientation)
            action = articulation_policy.get_next_articulation_action(dt)
            robot.apply_action(action)
            world.step(render=not args.headless)

        print(f"[OK] tracked a moving obstacle for {args.steps} steps")
        return 0
    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
