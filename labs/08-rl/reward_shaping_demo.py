"""8.4 - Reward shaping: sparse vs dense vs potential-based shaping.

Toy: 1D grid world with 21 cells. Agent starts at cell 0, goal at cell 16.
Each step: action in {-1, 0, +1}. Horizon = 40.

Three reward functions trained with **identical** tabular Q-learning:
  (a) sparse  : +1 only at the goal, 0 elsewhere
  (b) dense   : negative distance each step (-|s - g|/n)
  (c) shaped  : sparse +1 at goal + Ng-Harada-Russell potential-based shaping
                r' = r + gamma * phi(s') - phi(s), phi(s) = -|s - g| * 0.05

Ng, Harada, Russell (1999) prove (c) preserves the optimal policy of (a).
The interesting fact is that all three eventually converge but at very
different speeds — sparse barely learns at 200 episodes, shaped converges fast.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/08-rl/reward_shaping_demo.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

N_CELLS = 21
START = 10
GOAL = 18
HORIZON = 30
EPISODES = 300
ACTIONS = [-1, 0, 1]
ALPHA = 0.3
GAMMA = 0.95
EPS_INIT, EPS_FINAL = 0.3, 0.05
POT_SCALE = 0.2  # potential magnitude; bigger = more aggressive shaping

OUT = Path("runs/08-rl/reward_shaping.json")
OUT.parent.mkdir(parents=True, exist_ok=True)


def step_env(s: int, a: int) -> tuple[int, bool]:
    # Boundaries reflect rather than absorb to avoid pathological clipping.
    proposed = s + a
    if proposed < 0 or proposed >= N_CELLS:
        proposed = s  # blocked move, no clipping reward loop
    s_next = int(proposed)
    done = s_next == GOAL
    return s_next, done


def phi(s: int) -> float:
    """Potential function: distance to goal scaled by POT_SCALE."""
    return -abs(s - GOAL) * POT_SCALE


def reward(kind: str, s: int, s_next: int, done: bool) -> float:
    if kind == "sparse":
        return 1.0 if done else 0.0
    if kind == "dense":
        return -abs(s_next - GOAL) / N_CELLS
    if kind == "shaped":
        r = 1.0 if done else 0.0
        return r + GAMMA * phi(s_next) - phi(s)
    raise ValueError(kind)


def train(kind: str, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    Q = np.zeros((N_CELLS, len(ACTIONS)))
    returns_per_ep = []
    for ep in range(EPISODES):
        eps = EPS_INIT + (EPS_FINAL - EPS_INIT) * (ep / EPISODES)
        s = START
        env_return = 0.0
        for _ in range(HORIZON):
            if rng.random() < eps:
                a_idx = int(rng.integers(0, len(ACTIONS)))
            else:
                # break ties randomly so the agent doesn't always pick -1
                qmax = Q[s].max()
                tied = np.flatnonzero(Q[s] >= qmax - 1e-9)
                a_idx = int(rng.choice(tied))
            a = ACTIONS[a_idx]
            s_next, done = step_env(s, a)
            r = reward(kind, s, s_next, done)
            target = r + GAMMA * (0.0 if done else Q[s_next].max())
            Q[s, a_idx] += ALPHA * (target - Q[s, a_idx])
            env_return += (1.0 if done else 0.0)  # unshaped sparse return
            s = s_next
            if done:
                break
        returns_per_ep.append(env_return)
    return returns_per_ep


def main() -> None:
    np.random.seed(0)
    seeds = [0, 1, 2]
    results = {}
    for kind in ["sparse", "dense", "shaped"]:
        curves = np.array([train(kind, s) for s in seeds])
        first_success = []
        for c in curves:
            idxs = np.where(c > 0)[0]
            first_success.append(int(idxs[0]) if len(idxs) > 0 else -1)
        results[kind] = {
            "mean_success_last20": float(curves[:, -20:].mean()),
            "mean_success_first50": float(curves[:, :50].mean()),
            "first_success_episode_per_seed": first_success,
            "curve_seed0": [float(v) for v in curves[0]],
        }

    OUT.write_text(json.dumps(results, indent=2))

    print(f"{'reward':>8} {'success%(first 50)':>20} {'success%(last 20)':>20}  first_succ")
    for k, r in results.items():
        print(f"{k:>8} {r['mean_success_first50']*100:>18.1f}%   "
              f"{r['mean_success_last20']*100:>17.1f}%   "
              f"{r['first_success_episode_per_seed']}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
