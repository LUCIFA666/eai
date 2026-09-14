"""Measure RMPflow action latency and joint tracking at a chosen control rate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=600)
    parser.add_argument("--control-hz", type=float, default=60.0)
    parser.add_argument("--max-substep", type=float, default=0.00334)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if min(args.steps, args.control_hz, args.max_substep) <= 0:
        return 2
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        from isaacsim.core.api import World
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
        world.reset()
        robot.initialize()

        config = load_supported_motion_policy_config("Franka", "RMPflow")
        config["maximum_substep_size"] = args.max_substep
        rmpflow = RmpFlow(**config)
        wrapper = ArticulationMotionPolicy(robot, rmpflow)
        target_position = np.array([0.5, 0.0, 0.7])
        target_orientation = np.array([0.0, 1.0, 0.0, 0.0])

        latencies_ms: list[float] = []
        tracking_errors: list[float] = []
        for _ in range(args.steps):
            rmpflow.set_end_effector_target(target_position, target_orientation)
            start = perf_counter()
            action = wrapper.get_next_articulation_action(dt)
            latencies_ms.append((perf_counter() - start) * 1000.0)
            robot.apply_action(action)
            world.step(render=not args.headless)

            if action.joint_positions is not None and action.joint_indices is not None:
                measured = robot.get_joint_positions()[action.joint_indices]
                tracking_errors.append(
                    float(np.max(np.abs(action.joint_positions - measured)))
                )

        summary = {
            "control_hz": args.control_hz,
            "control_dt_s": dt,
            "maximum_substep_size_s": args.max_substep,
            "steps": args.steps,
            "policy_latency_ms_mean": float(np.mean(latencies_ms)),
            "policy_latency_ms_max": float(np.max(latencies_ms)),
            "joint_tracking_error_rad_max": (
                float(np.max(tracking_errors)) if tracking_errors else None
            ),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return 0
    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
