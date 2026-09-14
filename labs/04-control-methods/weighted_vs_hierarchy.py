"""Weighted and strict-priority task control demo for section 4.3.2.

The robot is a planar three-link arm.  Both controllers track an end-effector
target and a preferred posture.  The weighted solver trades tasks continuously;
the hierarchical solver projects the posture task into the primary task's
nullspace.  This is a kinematic teaching model, not a torque-level WBC.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


LINKS = np.array([0.8, 0.65, 0.45])


def forward_kinematics(q: np.ndarray) -> np.ndarray:
    cumulative = np.cumsum(q)
    return np.array([np.sum(LINKS * np.cos(cumulative)), np.sum(LINKS * np.sin(cumulative))])


def jacobian(q: np.ndarray) -> np.ndarray:
    cumulative = np.cumsum(q)
    j = np.zeros((2, 3))
    for column in range(3):
        j[0, column] = -np.sum(LINKS[column:] * np.sin(cumulative[column:]))
        j[1, column] = np.sum(LINKS[column:] * np.cos(cumulative[column:]))
    return j


def weighted_velocity(q: np.ndarray, target: np.ndarray, q_ref: np.ndarray) -> np.ndarray:
    j = jacobian(q)
    ee_command = 3.0 * (target - forward_kinematics(q))
    posture_command = 0.8 * (q_ref - q)
    w_ee, w_posture, damping = 12.0, 0.8, 1e-3
    matrix = np.vstack((w_ee * j, w_posture * np.eye(3), np.sqrt(damping) * np.eye(3)))
    vector = np.r_[w_ee * ee_command, w_posture * posture_command, np.zeros(3)]
    return np.linalg.lstsq(matrix, vector, rcond=None)[0]


def hierarchical_velocity(q: np.ndarray, target: np.ndarray, q_ref: np.ndarray) -> np.ndarray:
    j = jacobian(q)
    ee_command = 3.0 * (target - forward_kinematics(q))
    posture_command = 0.8 * (q_ref - q)
    j_pinv = np.linalg.pinv(j, rcond=1e-5)
    primary = j_pinv @ ee_command
    nullspace = np.eye(3) - j_pinv @ j
    secondary = nullspace @ np.linalg.pinv(nullspace, rcond=1e-5) @ (posture_command - primary)
    return primary + secondary


def simulate(controller, q0: np.ndarray, target: np.ndarray, q_ref: np.ndarray, dt: float, steps: int, vmax: float):
    q = q0.copy()
    q_log, ee_log, ee_error, posture_error = [q.copy()], [forward_kinematics(q)], [], []
    for _ in range(steps):
        velocity = controller(q, target, q_ref)
        velocity = np.clip(velocity, -vmax, vmax)
        q = q + dt * velocity
        ee = forward_kinematics(q)
        q_log.append(q.copy())
        ee_log.append(ee)
        ee_error.append(np.linalg.norm(target - ee))
        posture_error.append(np.linalg.norm(q_ref - q))
    return np.asarray(q_log), np.asarray(ee_log), np.asarray(ee_error), np.asarray(posture_error)


def draw_arm(axis, q: np.ndarray, color: str, label: str) -> None:
    cumulative = np.cumsum(q)
    points = np.zeros((4, 2))
    for index in range(3):
        points[index + 1] = points[index] + LINKS[index] * np.array([np.cos(cumulative[index]), np.sin(cumulative[index])])
    axis.plot(points[:, 0], points[:, 1], "o-", color=color, linewidth=3, label=label)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--steps", type=int, default=260)
    parser.add_argument("--max-velocity", type=float, default=1.5)
    parser.add_argument("--output", type=Path, default=Path("weighted_vs_hierarchy.png"))
    args = parser.parse_args()

    q0 = np.array([-0.55, 1.25, 0.35])
    q_ref = np.array([0.15, -0.45, 0.55])
    target = np.array([1.42, 0.82])
    weighted = simulate(weighted_velocity, q0, target, q_ref, args.dt, args.steps, args.max_velocity)
    hierarchy = simulate(hierarchical_velocity, q0, target, q_ref, args.dt, args.steps, args.max_velocity)

    print(f"weighted_final_ee_error={weighted[2][-1]:.6f}")
    print(f"hierarchy_final_ee_error={hierarchy[2][-1]:.6f}")
    print(f"weighted_final_posture_error={weighted[3][-1]:.6f}")
    print(f"hierarchy_final_posture_error={hierarchy[3][-1]:.6f}")

    time = np.arange(args.steps) * args.dt
    fig, axes = plt.subplots(1, 3, figsize=(14.0, 4.5), constrained_layout=True)
    axes[0].plot(weighted[1][:, 0], weighted[1][:, 1], color="#ef8354", label="weighted EE")
    axes[0].plot(hierarchy[1][:, 0], hierarchy[1][:, 1], color="#0b6e69", label="hierarchical EE")
    draw_arm(axes[0], weighted[0][-1], "#ef8354", "weighted final")
    draw_arm(axes[0], hierarchy[0][-1], "#0b6e69", "hierarchical final")
    axes[0].scatter(*target, marker="*", s=170, color="#f4b942", edgecolor="#6f4a00", zorder=5, label="target")
    axes[0].set(xlabel="x [m]", ylabel="y [m]", title="Task-space trajectories")
    axes[0].set_aspect("equal")
    axes[0].legend(fontsize=8)

    axes[1].semilogy(time, weighted[2], color="#ef8354", label="weighted")
    axes[1].semilogy(time, hierarchy[2], color="#0b6e69", label="hierarchical")
    axes[1].set(xlabel="time [s]", ylabel="end-effector error [m]", title="Primary task residual")
    axes[1].legend()

    axes[2].plot(time, weighted[3], color="#ef8354", label="weighted")
    axes[2].plot(time, hierarchy[3], color="#0b6e69", label="hierarchical")
    axes[2].set(xlabel="time [s]", ylabel="posture error [rad]", title="Secondary task residual")
    axes[2].legend()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=170)
    print(f"saved={args.output.resolve()}")


if __name__ == "__main__":
    main()
