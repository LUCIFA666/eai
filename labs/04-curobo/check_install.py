"""Verify a minimal cuRoboV2 installation on one CUDA device."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

import torch

from curobo.kinematics import Kinematics, KinematicsCfg
from curobo.types import JointState


def package_version() -> str:
    """Return the installed package version without relying on module globals."""
    try:
        return version("nvidia-curobo")
    except PackageNotFoundError:
        return "unknown"


def main() -> None:
    """Print environment facts and run one Franka forward-kinematics query."""
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; install a CUDA-enabled PyTorch build")

    print(f"curobo={package_version()}")
    print(f"torch={torch.__version__}")
    print(f"torch_cuda={torch.version.cuda}")
    print(f"visible_cuda_devices={torch.cuda.device_count()}")
    print(f"device_0={torch.cuda.get_device_name(0)}")

    robot = Kinematics(KinematicsCfg.from_robot_yaml_file("franka.yml"))
    position = torch.zeros(
        1,
        robot.get_dof(),
        device="cuda",
        dtype=torch.float32,
    )
    state = robot.compute_kinematics(
        JointState.from_position(position, joint_names=robot.joint_names)
    )
    tool_pose = state.tool_poses.get_link_pose(robot.tool_frames[0])

    if not torch.isfinite(tool_pose.position).all():
        raise RuntimeError("Forward kinematics returned a non-finite position")
    if not torch.isfinite(tool_pose.quaternion).all():
        raise RuntimeError("Forward kinematics returned a non-finite quaternion")

    print(f"dof={robot.get_dof()}")
    print(f"tool_frames={robot.tool_frames}")
    print(f"tool_position_shape={tuple(tool_pose.position.shape)}")
    print("status=ok")


if __name__ == "__main__":
    main()
