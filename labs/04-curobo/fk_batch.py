"""Benchmark batched Franka forward kinematics with cuRoboV2."""

from __future__ import annotations

import argparse
import json

import torch

from curobo.kinematics import Kinematics, KinematicsCfg
from curobo.types import JointState


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    """Run one warmup and one timed batched-FK query."""
    args = parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be positive")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")

    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    robot = Kinematics(KinematicsCfg.from_robot_yaml_file("franka.yml"))
    position = torch.rand(
        args.batch_size,
        robot.get_dof(),
        device="cuda",
        dtype=torch.float32,
    )
    joint_state = JointState.from_position(position, joint_names=robot.joint_names)

    robot.compute_kinematics(joint_state)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()

    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    state = robot.compute_kinematics(joint_state)
    end.record()
    torch.cuda.synchronize()

    tool_pose = state.tool_poses.get_link_pose(robot.tool_frames[0])
    if not torch.isfinite(tool_pose.position).all():
        raise RuntimeError("Batched FK returned non-finite positions")

    summary = {
        "batch_size": args.batch_size,
        "seed": args.seed,
        "dof": robot.get_dof(),
        "joint_state_shape": list(position.shape),
        "tool_position_shape": list(tool_pose.position.shape),
        "elapsed_ms": start.elapsed_time(end),
        "peak_memory_mib": torch.cuda.max_memory_allocated() / 1024**2,
        "device": torch.cuda.get_device_name(0),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
