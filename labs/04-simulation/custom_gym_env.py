"""4.11 — Custom Gymnasium environment template.

This is the reference custom env used in section 4.11. It models a 2D
point robot that must navigate to a goal while avoiding an obstacle.
We follow the modern ``gymnasium.Env`` contract exactly so it passes
``gymnasium.utils.env_checker.check_env``.

Run:
    python labs/04-simulation/custom_gym_env.py

It writes JSON metrics to ``runs/04-simulation/custom_gym_env.json`` and
an episode trajectory plot SVG to ``runs/04-simulation/custom_gym_env.svg``.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError as exc:  # pragma: no cover - environment guard
    raise RuntimeError("gymnasium missing; install via `pip install gymnasium`") from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS_LABEL = "runs/04-simulation"
try:
    RUNS.mkdir(parents=True, exist_ok=True)
except OSError:
    # Read-only filesystem (e.g. CI sandbox); fall back to $TMPDIR.
    import os, tempfile
    RUNS = (
        Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
        / "embodied-ai-04-simulation"
    )
    RUNS_LABEL = "$TMPDIR/embodied-ai-04-simulation"
    RUNS.mkdir(parents=True, exist_ok=True)
    print(f"[warn] runs/ is read-only; writing to {RUNS_LABEL}")


@dataclass
class PointNavConfig:
    arena_size: float = 1.0
    goal_radius: float = 0.1
    obstacle_radius: float = 0.18
    max_steps: int = 200
    dt: float = 0.05
    action_scale: float = 0.1  # max distance per step
    crash_penalty: float = -1.0
    success_reward: float = 1.0


class PointNavEnv(gym.Env):
    """A 2D point-goal navigation env: minimal but spec-compliant."""

    metadata = {"render_modes": ["ansi"], "render_fps": 20}

    def __init__(self, cfg: PointNavConfig | None = None, render_mode: str | None = None):
        super().__init__()
        self.cfg = cfg or PointNavConfig()
        self.render_mode = render_mode
        # Observation: agent_xy (2) + goal_xy (2) + obstacle_xy (2) = 6
        self.observation_space = spaces.Box(
            low=-self.cfg.arena_size,
            high=self.cfg.arena_size,
            shape=(6,),
            dtype=np.float32,
        )
        # Action: dx, dy in [-1, 1], scaled by cfg.action_scale internally.
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
        self._agent = np.zeros(2, dtype=np.float32)
        self._goal = np.zeros(2, dtype=np.float32)
        self._obstacle = np.zeros(2, dtype=np.float32)
        self._step_count = 0

    # --- gymnasium API -------------------------------------------------
    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        rng = self.np_random
        s = self.cfg.arena_size * 0.9
        # Sample agent, goal far enough apart, and an obstacle in between.
        self._agent = rng.uniform(-s, s, size=2).astype(np.float32)
        for _ in range(50):
            self._goal = rng.uniform(-s, s, size=2).astype(np.float32)
            if np.linalg.norm(self._goal - self._agent) > 0.5:
                break
        midpoint = 0.5 * (self._agent + self._goal)
        self._obstacle = (midpoint + rng.uniform(-0.1, 0.1, size=2)).astype(np.float32)
        self._step_count = 0
        return self._obs(), {"goal_dist": float(np.linalg.norm(self._goal - self._agent))}

    def step(self, action):
        action = np.asarray(action, dtype=np.float32).reshape(2)
        action = np.clip(action, -1.0, 1.0)
        delta = action * self.cfg.action_scale
        self._agent = np.clip(self._agent + delta, -self.cfg.arena_size, self.cfg.arena_size)
        self._step_count += 1

        dist_goal = float(np.linalg.norm(self._goal - self._agent))
        dist_obs = float(np.linalg.norm(self._obstacle - self._agent))
        success = dist_goal < self.cfg.goal_radius
        crashed = dist_obs < self.cfg.obstacle_radius
        truncated = self._step_count >= self.cfg.max_steps
        terminated = bool(success or crashed)

        # Shaped reward: -distance step cost, plus terminal bonuses.
        reward = -dist_goal * self.cfg.dt
        if success:
            reward += self.cfg.success_reward
        if crashed:
            reward += self.cfg.crash_penalty

        info = {
            "is_success": bool(success),
            "is_crash": bool(crashed),
            "goal_dist": dist_goal,
            "obstacle_dist": dist_obs,
            "step": self._step_count,
        }
        return self._obs(), float(reward), terminated, truncated, info

    def render(self):
        if self.render_mode == "ansi":
            return f"agent={self._agent.tolist()} goal={self._goal.tolist()}"
        return None

    def _obs(self) -> np.ndarray:
        return np.concatenate([self._agent, self._goal, self._obstacle]).astype(np.float32)


def random_policy(env: PointNavEnv, n_episodes: int, seed: int) -> dict:
    """Sample uniformly random actions."""
    rng = np.random.default_rng(seed)
    succ, crash, lengths, returns = 0, 0, [], []
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        ep_ret, t = 0.0, 0
        while True:
            action = rng.uniform(-1, 1, size=2).astype(np.float32)
            obs, r, term, trunc, info = env.step(action)
            ep_ret += r
            t += 1
            if term or trunc:
                break
        if info.get("is_success"):
            succ += 1
        if info.get("is_crash"):
            crash += 1
        lengths.append(t)
        returns.append(ep_ret)
    return {
        "policy": "random",
        "episodes": n_episodes,
        "success_rate": succ / n_episodes,
        "crash_rate": crash / n_episodes,
        "mean_length": float(np.mean(lengths)),
        "mean_return": float(np.mean(returns)),
    }


def greedy_policy(env: PointNavEnv, n_episodes: int, seed: int) -> dict:
    """Move directly toward goal, with naive obstacle deflection."""
    succ, crash, lengths, returns, traj = 0, 0, [], [], []
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        ep_ret, t, this_traj = 0.0, 0, [tuple(env._agent.tolist())]
        while True:
            agent = obs[:2]
            goal = obs[2:4]
            obstacle = obs[4:6]
            to_goal = goal - agent
            n = np.linalg.norm(to_goal) + 1e-9
            heading = to_goal / n
            to_obs = obstacle - agent
            d_obs = np.linalg.norm(to_obs) + 1e-9
            if d_obs < 0.35 and np.dot(to_obs / d_obs, heading) > 0:
                # Deflect 90° away from obstacle.
                perp = np.array([-to_obs[1], to_obs[0]]) / d_obs
                heading = 0.5 * heading + 0.5 * perp
                heading = heading / (np.linalg.norm(heading) + 1e-9)
            action = np.clip(heading, -1, 1).astype(np.float32)
            obs, r, term, trunc, info = env.step(action)
            ep_ret += r
            t += 1
            this_traj.append(tuple(env._agent.tolist()))
            if term or trunc:
                break
        if info.get("is_success"):
            succ += 1
        if info.get("is_crash"):
            crash += 1
        lengths.append(t)
        returns.append(ep_ret)
        traj.append(
            {"success": bool(info.get("is_success")), "path": this_traj, "goal": list(map(float, env._goal)), "obstacle": list(map(float, env._obstacle))}
        )
    return {
        "policy": "greedy",
        "episodes": n_episodes,
        "success_rate": succ / n_episodes,
        "crash_rate": crash / n_episodes,
        "mean_length": float(np.mean(lengths)),
        "mean_return": float(np.mean(returns)),
        "trajectories": traj,
    }


def write_svg(greedy_result: dict, out: Path) -> None:
    eps = greedy_result["trajectories"][:4]
    s = 1.0
    width, height = 500, 500

    def to_px(p):
        x = (p[0] + s) / (2 * s) * width
        y = (1 - (p[1] + s) / (2 * s)) * height
        return x, y

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfcfe" stroke="#d8dee7"/>',
    ]
    colors = ["#0f766e", "#dc2626", "#1d4ed8", "#9333ea"]
    for i, ep in enumerate(eps):
        col = colors[i % len(colors)]
        # goal
        gx, gy = to_px(ep["goal"])
        lines.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="14" fill="none" stroke="{col}" stroke-dasharray="4 3"/>')
        # obstacle
        ox, oy = to_px(ep["obstacle"])
        lines.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="26" fill="#fee2e2" stroke="#b91c1c"/>')
        # path
        pts = [to_px(p) for p in ep["path"]]
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        lines.append(f'<polyline points="{path}" fill="none" stroke="{col}" stroke-width="2"/>')
        if pts:
            ax, ay = pts[0]
            lines.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="5" fill="{col}"/>')
    lines.append('<text x="14" y="22" font-size="14" fill="#17202a">PointNavEnv greedy baseline (4 episodes)</text>')
    lines.append("</svg>")
    out.write_text("\n".join(lines))


def main() -> None:
    cfg = PointNavConfig()
    env = PointNavEnv(cfg)
    # API self-check via gymnasium utility.
    try:
        from gymnasium.utils.env_checker import check_env  # type: ignore

        check_env(env, skip_render_check=True)
        check_msg = "passed gymnasium.utils.env_checker.check_env"
    except Exception as exc:  # pragma: no cover - report but do not fail
        check_msg = f"check_env warning: {exc}"

    rand_stats = random_policy(env, n_episodes=20, seed=2024)
    greedy_stats = greedy_policy(env, n_episodes=20, seed=2024)

    print(f"[env-check] {check_msg}")
    print("[random] " + json.dumps({k: v for k, v in rand_stats.items() if k != "trajectories"}))
    print("[greedy] " + json.dumps({k: v for k, v in greedy_stats.items() if k != "trajectories"}))

    out_json = RUNS / "custom_gym_env.json"
    out_json.write_text(
        json.dumps(
            {
                "env_check": check_msg,
                "config": cfg.__dict__,
                "random": {k: v for k, v in rand_stats.items() if k != "trajectories"},
                "greedy": {k: v for k, v in greedy_stats.items() if k != "trajectories"},
            },
            indent=2,
        )
    )
    write_svg(greedy_stats, RUNS / "custom_gym_env.svg")
    print(f"[write] {RUNS_LABEL}/custom_gym_env.json")
    print(f"[write] {RUNS_LABEL}/custom_gym_env.svg")


if __name__ == "__main__":
    main()
