"""8.2 - Train PPO on CartPole-v1 with stable-baselines3.

50k env steps, 4 parallel envs, evaluate over 20 episodes with deterministic
policy, dump metrics to runs/08-rl/ppo_cartpole_metrics.json.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/08-rl/ppo_cartpole.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

OUT_DIR = Path("runs/08-rl")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.env_util import make_vec_env
        from stable_baselines3.common.evaluation import evaluate_policy
    except ImportError as e:
        msg = {"status": "skipped", "reason": f"stable-baselines3 not installed: {e}"}
        (OUT_DIR / "ppo_cartpole_metrics.json").write_text(json.dumps(msg, indent=2))
        print("stable-baselines3 not installed; skipping.")
        sys.exit(0)

    SEED = 0
    TOTAL_TIMESTEPS = 50_000
    N_ENVS = 4

    train_env = make_vec_env("CartPole-v1", n_envs=N_ENVS, seed=SEED)
    eval_env = make_vec_env("CartPole-v1", n_envs=1, seed=SEED + 100)

    model = PPO(
        "MlpPolicy",
        train_env,
        learning_rate=3e-4,
        n_steps=128,
        batch_size=64,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.0,
        verbose=0,
        seed=SEED,
    )

    t0 = time.time()
    model.learn(total_timesteps=TOTAL_TIMESTEPS, progress_bar=False)
    wall = time.time() - t0

    mean_ret, std_ret = evaluate_policy(model, eval_env, n_eval_episodes=20,
                                        deterministic=True)
    metrics = {
        "status": "ok",
        "env": "CartPole-v1",
        "algo": "PPO",
        "n_envs": N_ENVS,
        "total_timesteps": TOTAL_TIMESTEPS,
        "eval_episodes": 20,
        "eval_return_mean": float(mean_ret),
        "eval_return_std": float(std_ret),
        "wall_clock_s": round(wall, 2),
        "steps_per_sec": int(TOTAL_TIMESTEPS / wall),
        "sb3_version": __import__("stable_baselines3").__version__,
    }
    out = OUT_DIR / "ppo_cartpole_metrics.json"
    out.write_text(json.dumps(metrics, indent=2))
    print(f"eval return     : {mean_ret:.1f} ± {std_ret:.1f} (max=500)")
    print(f"wall clock      : {wall:.1f}s  ({metrics['steps_per_sec']} steps/s)")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
