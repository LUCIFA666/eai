"""Visualize RMPflow state and optionally demonstrate poor PD tracking."""

from __future__ import annotations

import argparse
import sys

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=900)
    parser.add_argument("--ignore-state-updates", action="store_true")
    parser.add_argument("--weaken-kp", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.steps <= 0:
        return 2
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": False})
    rmpflow = None
    try:
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import FixedCuboid
        from isaacsim.core.prims import Articulation
        from isaacsim.core.utils.nucleus import get_assets_root_path
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.robot_motion.motion_generation import (
            ArticulationMotionPolicy,
            RmpFlow,
        )
        from isaacsim.robot_motion.motion_generation.interface_config_loader import (
            load_supported_motion_policy_config,
        )

        dt = 1.0 / 60.0
        world = World(stage_units_in_meters=1.0, physics_dt=dt, rendering_dt=dt)
        world.scene.add_default_ground_plane()
        assets_root = get_assets_root_path()
        if assets_root is None:
            raise RuntimeError("Isaac Sim assets root is unavailable")
        add_reference_to_stage(
            assets_root + "/Isaac/Robots/Franka/franka.usd", "/World/Franka"
        )
        robot = Articulation("/World/Franka")
        obstacle = world.scene.add(
            FixedCuboid(
                prim_path="/World/obstacle",
                name="obstacle",
                position=np.array([0.42, 0.0, 0.62]),
                size=0.08,
                color=np.array([0.0, 0.2, 1.0]),
            )
        )
        world.reset()
        robot.initialize()

        config = load_supported_motion_policy_config("Franka", "RMPflow")
        rmpflow = RmpFlow(**config)
        rmpflow.add_obstacle(obstacle)
        rmpflow.set_ignore_state_updates(args.ignore_state_updates)
        rmpflow.visualize_collision_spheres()
        rmpflow.visualize_end_effector_position()
        wrapper = ArticulationMotionPolicy(robot, rmpflow)

        controller = robot.get_articulation_controller()
        original_kps, original_kds = controller.get_gains()
        if args.weaken_kp:
            controller.set_gains(kps=original_kps / 50.0, kds=original_kds)

        target_position = np.array([0.55, 0.0, 0.68])
        target_orientation = np.array([0.0, 1.0, 0.0, 0.0])
        for _ in range(args.steps):
            rmpflow.set_end_effector_target(target_position, target_orientation)
            rmpflow.update_world()
            action = wrapper.get_next_articulation_action(dt)
            robot.apply_action(action)
            world.step(render=True)

        if args.weaken_kp:
            controller.set_gains(kps=original_kps, kds=original_kds)
        print("[OK] debugging visualization completed")
        return 0
    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        if rmpflow is not None:
            rmpflow.stop_visualizing_collision_spheres()
            rmpflow.stop_visualizing_end_effector()
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
