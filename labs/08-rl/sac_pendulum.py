"""8.3 - Train SAC on Pendulum-v1 with stable-baselines3.

Pendulum-v1 has continuous actions (torque in [-2, 2]) and reward in [-16, 0].
A well-tuned SAC reaches ~ -150 in 10k-20k steps. We train 15k steps to keep
wall-clock < 2 min on CPU.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/08-rl/sac_pendulum.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

OUT_DIR = Path("runs/08-rl")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    try:
        from stable_baselines3 import SAC
        from stable_baselines3.common.env_util import make_vec_env
        from stable_baselines3.common.evaluation import evaluate_policy
    except ImportError as e:
        msg = {"status": "skipped", "reason": f"stable-baselines3 not installed: {e}"}
        (OUT_DIR / "sac_pendulum_metrics.json").write_text(json.dumps(msg, indent=2))
        print("stable-baselines3 not installed; skipping.")
        sys.exit(0)

    SEED = 0
    TOTAL_TIMESTEPS = 15_000

    train_env = make_vec_env("Pendulum-v1", n_envs=1, seed=SEED)
    eval_env = make_vec_env("Pendulum-v1", n_envs=1, seed=SEED + 100)

    model = SAC(
        "MlpPolicy",
        train_env,
        learning_rate=3e-4,
        buffer_size=20_000,
        learning_starts=1_000,
        batch_size=256,
        tau=0.005,
        gamma=0.99,
        train_freq=1,
        gradient_steps=1,
        seed=SEED,
        verbose=0,
    )

    t0 = time.time()
    model.learn(total_timesteps=TOTAL_TIMESTEPS, progress_bar=False)
    wall = time.time() - t0

    mean_ret, std_ret = evaluate_policy(model, eval_env, n_eval_episodes=20,
                                        deterministic=True)
    metrics = {
        "status": "ok",
        "env": "Pendulum-v1",
        "algo": "SAC",
        "total_timesteps": TOTAL_TIMESTEPS,
        "eval_episodes": 20,
        "eval_return_mean": float(mean_ret),
        "eval_return_std": float(std_ret),
        "wall_clock_s": round(wall, 2),
        "steps_per_sec": int(TOTAL_TIMESTEPS / wall),
        "sb3_version": __import__("stable_baselines3").__version__,
    }
    out = OUT_DIR / "sac_pendulum_metrics.json"
    out.write_text(json.dumps(metrics, indent=2))
    # Pendulum reward is per-step in [-16, 0]; well-trained ~ -150 over 200 steps.
    print(f"eval return     : {mean_ret:.1f} ± {std_ret:.1f}  (better -> closer to 0)")
    print(f"wall clock      : {wall:.1f}s  ({metrics['steps_per_sec']} steps/s)")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
