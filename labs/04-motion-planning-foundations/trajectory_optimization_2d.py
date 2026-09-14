"""Small trajectory-optimization demo used by section 4.1.3.

It optimizes internal 2-D waypoints with a smoothness term and a hinge loss on
signed obstacle clearance.  The implementation is intentionally transparent,
not a replacement for CHOMP, TrajOpt, STOMP, or cuRobo.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


CENTERS = np.array([[0.50, 0.50], [0.70, 0.70]])
RADII = np.array([0.18, 0.11])


def obstacle_cost_and_gradient(path: np.ndarray, margin: float) -> tuple[float, np.ndarray]:
    delta = path[:, None, :] - CENTERS[None, :, :]
    norm = np.linalg.norm(delta, axis=2)
    signed = norm - RADII[None, :]
    active = signed < margin
    hinge = np.where(active, margin - signed, 0.0)
    cost = float(np.sum(hinge**2))
    safe_norm = np.maximum(norm, 1e-9)
    direction = delta / safe_norm[:, :, None]
    gradient = np.sum(np.where(active[:, :, None], -2.0 * hinge[:, :, None] * direction, 0.0), axis=1)
    return cost, gradient


def smoothness_cost_and_gradient(path: np.ndarray) -> tuple[float, np.ndarray]:
    second_difference = path[:-2] - 2.0 * path[1:-1] + path[2:]
    cost = float(np.sum(second_difference**2))
    gradient = np.zeros_like(path)
    gradient[:-2] += 2.0 * second_difference
    gradient[1:-1] -= 4.0 * second_difference
    gradient[2:] += 2.0 * second_difference
    return cost, gradient


def minimum_clearance(path: np.ndarray) -> float:
    distance = np.linalg.norm(path[:, None, :] - CENTERS[None, :, :], axis=2) - RADII[None, :]
    return float(distance.min())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=900)
    parser.add_argument("--step-size", type=float, default=0.015)
    parser.add_argument("--margin", type=float, default=0.055)
    parser.add_argument("--obstacle-weight", type=float, default=28.0)
    parser.add_argument("--smoothness-weight", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=Path("trajectory_optimization.png"))
    args = parser.parse_args()

    start = np.array([0.08, 0.10])
    goal = np.array([0.92, 0.90])
    alpha = np.linspace(0.0, 1.0, 70)[:, None]
    initial = (1.0 - alpha) * start + alpha * goal
    initial[:, 1] += 0.06 * np.sin(np.pi * alpha[:, 0])  # break exact symmetry
    path = initial.copy()

    for iteration in range(args.iterations):
        smooth_cost, smooth_gradient = smoothness_cost_and_gradient(path)
        obstacle_cost, obstacle_gradient = obstacle_cost_and_gradient(path, args.margin)
        gradient = args.smoothness_weight * smooth_gradient + args.obstacle_weight * obstacle_gradient
        gradient[0] = 0.0
        gradient[-1] = 0.0
        gradient_norm = np.linalg.norm(gradient[1:-1], axis=1, keepdims=True)
        gradient[1:-1] /= np.maximum(1.0, gradient_norm / 4.0)
        path[1:-1] -= args.step_size * gradient[1:-1]
        path[1:-1] = np.clip(path[1:-1], 0.0, 1.0)
        if iteration in (0, args.iterations // 2, args.iterations - 1):
            total = args.smoothness_weight * smooth_cost + args.obstacle_weight * obstacle_cost
            print(f"iteration={iteration:04d} total_cost={total:.6f} clearance={minimum_clearance(path):.4f}")

    fig, ax = plt.subplots(figsize=(7.2, 6.3), constrained_layout=True)
    for center, radius in zip(CENTERS, RADII):
        ax.add_patch(plt.Circle(center, radius, color="#ef8354", alpha=0.88))
        ax.add_patch(plt.Circle(center, radius + args.margin, color="#ef8354", alpha=0.12))
    ax.plot(initial[:, 0], initial[:, 1], "--", color="#7a8793", linewidth=2, label="initial seed")
    ax.plot(path[:, 0], path[:, 1], color="#0b6e69", linewidth=3.5, label="optimized path")
    ax.scatter(*start, color="#247ba0", s=80, zorder=5)
    ax.scatter(*goal, color="#f4b942", edgecolor="#6f4a00", s=90, zorder=5)
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="q1", ylabel="q2", title="Smoothness + obstacle-clearance optimization")
    ax.set_aspect("equal")
    ax.legend()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=170)
    print(f"minimum_clearance={minimum_clearance(path):.4f}")
    print(f"saved={args.output.resolve()}")


if __name__ == "__main__":
    main()
