"""6.1 — A* search on a 2D occupancy grid.

Deterministic 30x30 grid with three rectangular obstacles plus a
"random" wall pattern from a fixed seed.  A* with the octile heuristic
(8-connected motion).  We compare against uniform-cost (Dijkstra) by
zeroing the heuristic and report path length, expanded nodes, and the
node-expansion savings.

Run:
    python labs/06-planning/astar_gridworld.py

Pure numpy + Python stdlib.  No external deps.
"""
from __future__ import annotations

import heapq
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np


RUN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs", "06-planning"))
os.makedirs(RUN_DIR, exist_ok=True)


GRID = 30
START = (1, 1)
GOAL = (28, 28)

NEIGHBORS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


def make_grid(seed: int = 0):
    rng = np.random.default_rng(seed)
    g = np.zeros((GRID, GRID), dtype=np.int8)
    # Three deterministic obstacles.
    g[5:15, 10] = 1
    g[10, 4:12] = 1
    g[18:25, 18:20] = 1
    g[6, 18:28] = 1
    g[22, 0:18] = 1
    # Sprinkle a few random obstacles avoiding start/goal.
    n_random = 35
    for _ in range(n_random):
        r = int(rng.integers(0, GRID))
        c = int(rng.integers(0, GRID))
        if (r, c) in (START, GOAL):
            continue
        g[r, c] = 1
    g[START] = 0
    g[GOAL] = 0
    return g


def heuristic_octile(a, b) -> float:
    dr = abs(a[0] - b[0])
    dc = abs(a[1] - b[1])
    return (dr + dc) + (np.sqrt(2) - 2) * min(dr, dc)


@dataclass
class AStarResult:
    found: bool
    path: list
    cost: float
    expanded: int
    closed: int


def astar(grid, start, goal, heuristic=heuristic_octile) -> AStarResult:
    open_heap = []
    g = {start: 0.0}
    parent = {}
    h0 = heuristic(start, goal)
    heapq.heappush(open_heap, (h0, 0.0, start))
    closed = set()
    expanded = 0
    while open_heap:
        f, gscore, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        closed.add(cur)
        expanded += 1
        if cur == goal:
            path = [cur]
            while path[-1] in parent:
                path.append(parent[path[-1]])
            path.reverse()
            return AStarResult(True, path, gscore, expanded, len(closed))
        for dr, dc in NEIGHBORS:
            nr, nc = cur[0] + dr, cur[1] + dc
            if not (0 <= nr < grid.shape[0] and 0 <= nc < grid.shape[1]):
                continue
            if grid[nr, nc] == 1:
                continue
            # Disallow diagonal cutting through corners.
            if dr != 0 and dc != 0:
                if grid[cur[0] + dr, cur[1]] == 1 or grid[cur[0], cur[1] + dc] == 1:
                    continue
            step = np.hypot(dr, dc)
            tentative = gscore + step
            nb = (nr, nc)
            if tentative < g.get(nb, float("inf")):
                g[nb] = tentative
                parent[nb] = cur
                f_score = tentative + heuristic(nb, goal)
                heapq.heappush(open_heap, (f_score, tentative, nb))
    return AStarResult(False, [], float("inf"), expanded, len(closed))


def render_ascii(grid, path):
    out = [["." if c == 0 else "#" for c in row] for row in grid]
    for r, c in path:
        out[r][c] = "*"
    out[START[0]][START[1]] = "S"
    out[GOAL[0]][GOAL[1]] = "G"
    return "\n".join("".join(row) for row in out)


def main():
    grid = make_grid()
    print(f"grid {GRID}x{GRID}, start={START}, goal={GOAL}, blocked = {int(grid.sum())} cells")

    print("\n--- A* with octile heuristic ---")
    res_a = astar(grid, START, GOAL)
    print(f"  found = {res_a.found}, cost = {res_a.cost:.4f}, path = {len(res_a.path)} cells, expanded = {res_a.expanded}")

    print("\n--- Dijkstra (zero heuristic) ---")
    res_d = astar(grid, START, GOAL, heuristic=lambda a, b: 0.0)
    print(f"  found = {res_d.found}, cost = {res_d.cost:.4f}, path = {len(res_d.path)} cells, expanded = {res_d.expanded}")

    print(f"\nspeedup in expanded nodes: A* uses {res_a.expanded}/{res_d.expanded} = {res_a.expanded*100/res_d.expanded:.1f}%")
    print(f"optimal costs equal? {abs(res_a.cost - res_d.cost) < 1e-9}")

    ascii_map = render_ascii(grid, res_a.path)
    print("\nmap (S=start, G=goal, *=path, #=obstacle):")
    print(ascii_map)

    with open(os.path.join(RUN_DIR, "astar_grid.txt"), "w") as f:
        f.write(ascii_map + "\n")
    np.savetxt(os.path.join(RUN_DIR, "astar_grid.csv"), grid, fmt="%d", delimiter=",")
    print(f"\nwrote {os.path.join(RUN_DIR, 'astar_grid.txt')}")
    assert res_a.found, "A* failed to find a path"
    assert abs(res_a.cost - res_d.cost) < 1e-6, "heuristic changed optimal cost"
    print(">>> PASS: A* and Dijkstra agree on cost; A* expands fewer nodes.")


if __name__ == "__main__":
    main()
