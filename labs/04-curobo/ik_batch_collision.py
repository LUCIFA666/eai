"""Solve a batch of collision-aware Franka IK targets with cuRoboV2."""

from __future__ import annotations

import argparse
import json

import torch

from curobo.inverse_kinematics import InverseKinematics, InverseKinematicsCfg
from curobo.types import GoalToolPose, Pose


def parse_args() -> argparse.Namespace:
    """Parse query batch and seed counts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--num-seeds", type=int, default=32)
    return parser.parse_args()


def main() -> None:
    """Run the official-style table-scene collision-aware IK batch."""
    args = parse_args()
    if args.batch_size < 1 or args.num_seeds < 1:
        raise ValueError("batch size and seed count must be positive")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")

    config = InverseKinematicsCfg.create(
        robot="franka.yml",
        scene_model="collision_table.yml",
        num_seeds=args.num_seeds,
        max_batch_size=args.batch_size,
        self_collision_check=True,
    )
    solver = InverseKinematics(config)
    target_link = solver.tool_frames[0]

    positions = torch.zeros(
        args.batch_size,
        3,
        device="cuda",
        dtype=torch.float32,
    )
    positions[:, 0] = torch.linspace(0.3, 0.7, args.batch_size, device="cuda")
    positions[:, 2] = 0.4

    quaternions = torch.zeros(
        args.batch_size,
        4,
        device="cuda",
        dtype=torch.float32,
    )
    quaternions[:, 0] = 1.0
    goal_poses = Pose(position=positions, quaternion=quaternions)
    goal = GoalToolPose.from_poses({target_link: goal_poses}, num_goalset=1)

    torch.cuda.reset_peak_memory_stats()
    result = solver.solve_pose(goal)
    success = result.success.squeeze()
    success_count = int(success.sum().item())

    successful_errors = result.position_error[success]
    summary = {
        "batch_size": args.batch_size,
        "num_seeds": args.num_seeds,
        "success_count": success_count,
        "success_rate": success_count / args.batch_size,
        "mean_position_error_mm": (
            float(successful_errors.mean().item() * 1000)
            if success_count
            else None
        ),
        "max_position_error_mm": (
            float(successful_errors.max().item() * 1000)
            if success_count
            else None
        ),
        "peak_memory_mib": torch.cuda.max_memory_allocated() / 1024**2,
        "device": torch.cuda.get_device_name(0),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if not success_count:
        raise RuntimeError("No collision-aware IK target was solved")


if __name__ == "__main__":
    main()
