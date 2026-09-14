"""Deterministic 2-D RRT demo used by section 4.1.2."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class Node:
    point: np.ndarray
    parent: int


OBSTACLES = np.array(
    [
        [0.45, 0.48, 0.16],
        [0.68, 0.72, 0.13],
        [0.27, 0.78, 0.11],
    ]
)


def state_is_valid(point: np.ndarray, robot_radius: float) -> bool:
    if np.any(point < 0.0) or np.any(point > 1.0):
        return False
    distance = np.linalg.norm(point[None, :] - OBSTACLES[:, :2], axis=1)
    return bool(np.all(distance > OBSTACLES[:, 2] + robot_radius))


def motion_is_valid(start: np.ndarray, goal: np.ndarray, resolution: float, robot_radius: float) -> bool:
    distance = float(np.linalg.norm(goal - start))
    count = max(2, int(np.ceil(distance / resolution)) + 1)
    for alpha in np.linspace(0.0, 1.0, count):
        if not state_is_valid((1.0 - alpha) * start + alpha * goal, robot_radius):
            return False
    return True


def reconstruct(nodes: list[Node], index: int) -> np.ndarray:
    path = []
    while index >= 0:
        path.append(nodes[index].point)
        index = nodes[index].parent
    return np.array(path[::-1])


def plan(seed: int, max_iterations: int, step_size: float, goal_bias: float, resolution: float) -> tuple[list[Node], np.ndarray]:
    rng = np.random.default_rng(seed)
    start = np.array([0.08, 0.08])
    goal = np.array([0.92, 0.90])
    robot_radius = 0.025
    nodes = [Node(start, -1)]

    for iteration in range(max_iterations):
        sample = goal if rng.random() < goal_bias else rng.random(2)
        points = np.stack([node.point for node in nodes])
        nearest_index = int(np.argmin(np.linalg.norm(points - sample, axis=1)))
        direction = sample - nodes[nearest_index].point
        norm = float(np.linalg.norm(direction))
        if norm < 1e-12:
            continue
        candidate = nodes[nearest_index].point + direction / norm * min(step_size, norm)
        if not motion_is_valid(nodes[nearest_index].point, candidate, resolution, robot_radius):
            continue
        nodes.append(Node(candidate, nearest_index))

        if np.linalg.norm(candidate - goal) <= step_size and motion_is_valid(candidate, goal, resolution, robot_radius):
            nodes.append(Node(goal, len(nodes) - 1))
            print(f"solved_iteration={iteration + 1}")
            return nodes, reconstruct(nodes, len(nodes) - 1)

    raise RuntimeError("RRT did not find a path; increase --max-iterations or inspect parameters")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-iterations", type=int, default=5000)
    parser.add_argument("--step-size", type=float, default=0.07)
    parser.add_argument("--goal-bias", type=float, default=0.08)
    parser.add_argument("--collision-resolution", type=float, default=0.01)
    parser.add_argument("--output", type=Path, default=Path("rrt_2d.png"))
    args = parser.parse_args()

    nodes, path = plan(
        args.seed,
        args.max_iterations,
        args.step_size,
        args.goal_bias,
        args.collision_resolution,
    )
    length = float(np.linalg.norm(np.diff(path, axis=0), axis=1).sum())
    print(f"tree_nodes={len(nodes)}")
    print(f"path_waypoints={len(path)}")
    print(f"path_length={length:.4f}")

    fig, ax = plt.subplots(figsize=(6.5, 6.5), constrained_layout=True)
    for node in nodes[1:]:
        parent = nodes[node.parent].point
        ax.plot([parent[0], node.point[0]], [parent[1], node.point[1]], color="#b8cbc6", linewidth=0.7)
    for x, y, radius in OBSTACLES:
        ax.add_patch(plt.Circle((x, y), radius + 0.025, color="#ef8354", alpha=0.82))
    ax.plot(path[:, 0], path[:, 1], color="#0b6e69", linewidth=3.5, label="first feasible path")
    ax.scatter(*path[0], color="#247ba0", s=80, label="start", zorder=5)
    ax.scatter(*path[-1], color="#f4b942", edgecolor="#6f4a00", s=90, label="goal", zorder=5)
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="q1", ylabel="q2", title="RRT in a 2-D configuration space")
    ax.set_aspect("equal")
    ax.legend(loc="lower right")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=170)
    print(f"saved={args.output.resolve()}")


if __name__ == "__main__":
    main()
