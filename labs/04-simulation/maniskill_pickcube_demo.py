"""4.6 — Minimal ManiSkill PickCube smoke test.

Gracefully handles the (very common) case where mani_skill / sapien
isn't installed: writes a ``.skipped`` marker and exits 1 so CI can
distinguish "skipped" from "passed".

Run:
    python labs/04-simulation/maniskill_pickcube_demo.py

Outputs (success case):
    runs/04-simulation/maniskill_pickcube.txt
Outputs (skipped case):
    runs/04-simulation/maniskill_pickcube.skipped
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs/04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)


def main() -> int:
    try:
        import gymnasium as gym
        import mani_skill.envs  # noqa: F401  registers all envs
        import sapien
    except ImportError as exc:
        msg = (
            f"mani_skill / sapien not installed in this env "
            f"({type(exc).__name__}: {exc!s}). "
            "To enable: pip install --index-url https://mirrors.aliyun.com/pypi/simple/ mani-skill"
        )
        print(msg)
        (RUNS / "maniskill_pickcube.skipped").write_text(msg + "\n", encoding="utf-8")
        return 1

    env = gym.make("PickCube-v1", obs_mode="state", control_mode="pd_ee_delta_pose",
                   render_mode="rgb_array")
    obs, info = env.reset(seed=0)
    rng_action = env.action_space.sample
    rewards = []
    for _ in range(50):
        a = rng_action()
        obs, r, term, trunc, info = env.step(a)
        rewards.append(float(r))
        if term or trunc:
            break
    env.close()

    summary = {
        "task": "PickCube-v1",
        "obs_dim": int(obs.shape[0]) if hasattr(obs, "shape") else "dict",
        "act_dim": env.action_space.shape[0],
        "sapien_version": str(sapien.__version__),
        "n_steps": len(rewards),
        "mean_reward_random": sum(rewards) / max(len(rewards), 1),
        "max_reward_random": max(rewards) if rewards else None,
    }
    txt = json.dumps(summary, indent=2)
    print(txt)
    (RUNS / "maniskill_pickcube.txt").write_text(txt + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
