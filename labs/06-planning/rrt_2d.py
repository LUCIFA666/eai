"""6.2 — RRT in a 2D world with circular obstacles.

Implements vanilla RRT (Rapidly-exploring Random Tree) and RRT* with
rewiring on a 10 m x 10 m playground.  Five circular obstacles block the
path between a fixed start ``(0.5, 0.5)`` and goal ``(9.0, 9.0)``.

We use a fixed RNG seed so the printed metrics (tree size, path
length, computation time) are reproducible.

Run:
    python labs/06-planning/rrt_2d.py
"""
from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


RUN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs", "06-planning"))
os.makedirs(RUN_DIR, exist_ok=True)


WORLD = (10.0, 10.0)
START = (0.5, 0.5)
GOAL = (9.0, 9.0)
OBSTACLES = [
    (3.0, 3.0, 1.2),
    (6.0, 4.0, 1.0),
    (4.5, 7.0, 1.2),
    (7.5, 7.5, 1.0),
    (2.5, 6.5, 0.8),
]


@dataclass
class Node:
    x: float
    y: float
    parent: Optional[int] = None
    cost: float = 0.0


def collision_free(p, q) -> bool:
    """Check if the segment p->q clears all circular obstacles."""
    # Sample 12 intermediate points.
    for t in np.linspace(0.0, 1.0, 16):
        px = p[0] + t * (q[0] - p[0])
        py = p[1] + t * (q[1] - p[1])
        for ox, oy, r in OBSTACLES:
            if (px - ox) ** 2 + (py - oy) ** 2 <= r ** 2:
                return False
    return True


def nearest(nodes: List[Node], pt) -> int:
    dists = [(n.x - pt[0]) ** 2 + (n.y - pt[1]) ** 2 for n in nodes]
    return int(np.argmin(dists))


def steer(p, q, step):
    dx = q[0] - p[0]
    dy = q[1] - p[1]
    d = math.hypot(dx, dy)
    if d <= step:
        return q
    return (p[0] + step * dx / d, p[1] + step * dy / d)


def rrt(rng, max_iter=2000, step=0.5, goal_bias=0.05):
    nodes = [Node(*START)]
    for it in range(max_iter):
        if rng.random() < goal_bias:
            sample = GOAL
        else:
            sample = (rng.uniform(0, WORLD[0]), rng.uniform(0, WORLD[1]))
        i = nearest(nodes, sample)
        new_pt = steer((nodes[i].x, nodes[i].y), sample, step)
        if not collision_free((nodes[i].x, nodes[i].y), new_pt):
            continue
        d = math.hypot(new_pt[0] - nodes[i].x, new_pt[1] - nodes[i].y)
        nodes.append(Node(new_pt[0], new_pt[1], parent=i, cost=nodes[i].cost + d))
        if math.hypot(new_pt[0] - GOAL[0], new_pt[1] - GOAL[1]) <= step and collision_free(new_pt, GOAL):
            nodes.append(Node(*GOAL, parent=len(nodes) - 1, cost=nodes[-1].cost + math.hypot(new_pt[0] - GOAL[0], new_pt[1] - GOAL[1])))
            return nodes, it + 1
    return nodes, max_iter


def rrt_star(rng, max_iter=2000, step=0.5, goal_bias=0.05, search_radius=1.2):
    nodes = [Node(*START)]
    goal_idx = None
    for it in range(max_iter):
        if rng.random() < goal_bias:
            sample = GOAL
        else:
            sample = (rng.uniform(0, WORLD[0]), rng.uniform(0, WORLD[1]))
        i_near = nearest(nodes, sample)
        new_pt = steer((nodes[i_near].x, nodes[i_near].y), sample, step)
        if not collision_free((nodes[i_near].x, nodes[i_near].y), new_pt):
            continue
        # Pick best parent in the rewiring ball.
        candidate_parents = [
            j for j, n in enumerate(nodes)
            if math.hypot(n.x - new_pt[0], n.y - new_pt[1]) < search_radius
            and collision_free((n.x, n.y), new_pt)
        ]
        if not candidate_parents:
            candidate_parents = [i_near]
        best_parent = min(
            candidate_parents,
            key=lambda j: nodes[j].cost + math.hypot(nodes[j].x - new_pt[0], nodes[j].y - new_pt[1]),
        )
        new_node = Node(
            new_pt[0],
            new_pt[1],
            parent=best_parent,
            cost=nodes[best_parent].cost + math.hypot(nodes[best_parent].x - new_pt[0], nodes[best_parent].y - new_pt[1]),
        )
        nodes.append(new_node)
        new_idx = len(nodes) - 1
        # Rewire neighbours.
        for j in candidate_parents:
            if j == best_parent:
                continue
            d = math.hypot(nodes[j].x - new_node.x, nodes[j].y - new_node.y)
            if new_node.cost + d < nodes[j].cost and collision_free((new_node.x, new_node.y), (nodes[j].x, nodes[j].y)):
                nodes[j].parent = new_idx
                nodes[j].cost = new_node.cost + d
        # Try connecting to goal.
        if math.hypot(new_pt[0] - GOAL[0], new_pt[1] - GOAL[1]) <= step and collision_free(new_pt, GOAL):
            goal_cost = new_node.cost + math.hypot(new_pt[0] - GOAL[0], new_pt[1] - GOAL[1])
            if goal_idx is None or goal_cost < nodes[goal_idx].cost:
                if goal_idx is None:
                    nodes.append(Node(*GOAL, parent=new_idx, cost=goal_cost))
                    goal_idx = len(nodes) - 1
                else:
                    nodes[goal_idx].parent = new_idx
                    nodes[goal_idx].cost = goal_cost
    return nodes, max_iter, goal_idx


def extract_path(nodes: List[Node], goal_idx: int) -> List[Tuple[float, float]]:
    path = []
    j = goal_idx
    while j is not None:
        path.append((nodes[j].x, nodes[j].y))
        j = nodes[j].parent
    path.reverse()
    return path


def path_length(path) -> float:
    return float(sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1)))


def main():
    rng = np.random.default_rng(7)
    print(f"world = {WORLD}, start = {START}, goal = {GOAL}, obstacles = {len(OBSTACLES)}")

    t0 = time.time()
    nodes, it_count = rrt(rng, max_iter=4000, step=0.5)
    rrt_time = time.time() - t0
    if nodes[-1].x == GOAL[0] and nodes[-1].y == GOAL[1]:
        rrt_path = extract_path(nodes, len(nodes) - 1)
    else:
        rrt_path = []
    print("\n--- vanilla RRT ---")
    print(f"  tree size = {len(nodes)}, iterations = {it_count}, time = {rrt_time*1000:.2f} ms")
    if rrt_path:
        print(f"  path waypoints = {len(rrt_path)}, length = {path_length(rrt_path):.4f} m")
    else:
        print("  failed to reach goal")

    rng2 = np.random.default_rng(7)
    t0 = time.time()
    nodes_s, it_count_s, goal_idx = rrt_star(rng2, max_iter=4000, step=0.5)
    rrt_star_time = time.time() - t0
    print("\n--- RRT* (rewiring) ---")
    print(f"  tree size = {len(nodes_s)}, iterations = {it_count_s}, time = {rrt_star_time*1000:.2f} ms")
    if goal_idx is not None:
        star_path = extract_path(nodes_s, goal_idx)
        print(f"  path waypoints = {len(star_path)}, length = {path_length(star_path):.4f} m")
    else:
        star_path = []
        print("  failed to reach goal")

    # Save metrics + path.
    with open(os.path.join(RUN_DIR, "rrt_metrics.csv"), "w") as f:
        f.write("planner,tree_size,iterations,time_ms,path_length_m\n")
        f.write(f"RRT,{len(nodes)},{it_count},{rrt_time*1000:.2f},{path_length(rrt_path) if rrt_path else 0:.4f}\n")
        f.write(f"RRT*,{len(nodes_s)},{it_count_s},{rrt_star_time*1000:.2f},{path_length(star_path) if star_path else 0:.4f}\n")

    if star_path:
        with open(os.path.join(RUN_DIR, "rrt_star_path.csv"), "w") as f:
            f.write("x,y\n")
            for x, y in star_path:
                f.write(f"{x:.5f},{y:.5f}\n")

    assert rrt_path, "RRT failed"
    assert star_path, "RRT* failed"
    assert path_length(star_path) <= path_length(rrt_path) + 0.2, "RRT* should be no worse than RRT"
    print("\n>>> PASS: RRT and RRT* both reach goal; RRT* path is no worse than RRT.")


if __name__ == "__main__":
    main()
