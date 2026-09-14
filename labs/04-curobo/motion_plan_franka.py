"""Generate one collision-free Franka trajectory with cuRoboV2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch

from curobo.motion_planner import MotionPlanner, MotionPlannerCfg
from curobo.types import GoalToolPose, JointState


def parse_args() -> argparse.Namespace:
    """Parse the optional JSON evidence path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def scalar(value: Any) -> float:
    """Convert a Python or one-element tensor scalar to float."""
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def shape_or_none(value: Any) -> list[int] | None:
    """Return a tensor shape when the optional trajectory field is present."""
    return list(value.shape) if value is not None else None


def main() -> None:
    """Warm up MotionPlanner, solve one pose request, and emit JSON evidence."""
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")

    config = MotionPlannerCfg.create(
        robot="franka.yml",
        scene_model="collision_test.yml",
    )
    planner = MotionPlanner(config)
    planner.warmup(enable_graph=True, num_warmup_iterations=5)

    start_state = JointState.from_position(
        planner.default_joint_state.position.unsqueeze(0),
        joint_names=planner.joint_names,
    )
    goal_pose = GoalToolPose(
        tool_frames=planner.tool_frames,
        position=torch.tensor(
            [[[[[0.5, 0.0, 0.3]]]]],
            device="cuda",
            dtype=torch.float32,
        ),
        quaternion=torch.tensor(
            [[[[[1.0, 0.0, 0.0, 0.0]]]]],
            device="cuda",
            dtype=torch.float32,
        ),
    )

    torch.cuda.reset_peak_memory_stats()
    result = planner.plan_pose(goal_pose, start_state)
    if result is None or not result.success.any():
        raise RuntimeError("Motion planning failed")

    interpolated = result.get_interpolated_plan()
    interpolation_dt = scalar(planner.trajopt_solver.config.interpolation_dt)
    waypoint_count = int(interpolated.position.shape[-2])

    if not torch.isfinite(interpolated.position).all():
        raise RuntimeError("Planned trajectory contains non-finite positions")

    summary = {
        "success": True,
        "device": torch.cuda.get_device_name(0),
        "planning_time_s": scalar(result.total_time),
        "waypoint_count": waypoint_count,
        "interpolation_dt_s": interpolation_dt,
        "trajectory_duration_s": waypoint_count * interpolation_dt,
        "position_shape": list(interpolated.position.shape),
        "velocity_shape": shape_or_none(interpolated.velocity),
        "acceleration_shape": shape_or_none(interpolated.acceleration),
        "joint_names": list(planner.joint_names),
        "peak_memory_mib": torch.cuda.max_memory_allocated() / 1024**2,
    }
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    print(payload)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
