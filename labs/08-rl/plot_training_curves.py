"""Generate training curve PNGs for all Chapter 9 experiments.

Runs the SB3 PPO (CartPole) and SAC (Pendulum) with epoch-level logging,
loads the reward-shaping JSON, and saves three plots into section/09-*/.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/08-rl/plot_training_curves.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path("runs/08-rl")
IMG_DIR = Path("section/09-reinforcement-learning-for-robotics")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 0


def plot_ppo_cartpole() -> None:
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.callbacks import BaseCallback

    class LogCallback(BaseCallback):
        def __init__(self):
            super().__init__()
            self.ep_returns: list[float] = []
            self.ep_steps: list[int] = []

        def _on_step(self) -> bool:
            infos = self.locals.get("infos", [])
            for info in infos:
                if "episode" in info:
                    self.ep_returns.append(info["episode"]["r"])
                    self.ep_steps.append(self.num_timesteps)
            return True

    train_env = make_vec_env("CartPole-v1", n_envs=4, seed=SEED)
    model = PPO(
        "MlpPolicy", train_env,
        learning_rate=3e-4, n_steps=128, batch_size=64,
        gamma=0.99, gae_lambda=0.95, clip_range=0.2, ent_coef=0.0,
        verbose=0, seed=SEED,
    )
    cb = LogCallback()
    model.learn(total_timesteps=50_000, callback=cb, progress_bar=False)

    fig, ax = plt.subplots(figsize=(7, 4))
    if cb.ep_returns:
        window = max(1, len(cb.ep_returns) // 15)
        smoothed = np.convolve(cb.ep_returns, np.ones(window) / window, mode="valid")
        ax.plot(cb.ep_steps[:len(smoothed)], smoothed, color="#0b6f64", linewidth=2,
                label=f"SB3 PPO (window={window})")
        ax.scatter(cb.ep_steps, cb.ep_returns, alpha=0.12, s=6, color="#69736e")
    ax.axhline(y=500, color="#9d650b", linestyle="--", alpha=0.7, label="Optimal (500)")
    ax.set_xlabel("Env Steps")
    ax.set_ylabel("Episode Return")
    ax.set_title("PPO (Stable-Baselines3) - CartPole-v1")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(IMG_DIR / "ppo_cartpole_curve.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {IMG_DIR / 'ppo_cartpole_curve.png'}")


def plot_sac_pendulum() -> None:
    from stable_baselines3 import SAC
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.callbacks import BaseCallback

    class LogCallback(BaseCallback):
        def __init__(self):
            super().__init__()
            self.ep_returns: list[float] = []
            self.ep_steps: list[int] = []

        def _on_step(self) -> bool:
            infos = self.locals.get("infos", [])
            for info in infos:
                if "episode" in info:
                    self.ep_returns.append(info["episode"]["r"])
                    self.ep_steps.append(self.num_timesteps)
            return True

    train_env = make_vec_env("Pendulum-v1", n_envs=1, seed=SEED)
    model = SAC(
        "MlpPolicy", train_env,
        learning_rate=3e-4, buffer_size=20_000, learning_starts=1_000,
        batch_size=256, tau=0.005, gamma=0.99,
        train_freq=1, gradient_steps=1, seed=SEED, verbose=0,
    )
    cb = LogCallback()
    model.learn(total_timesteps=15_000, callback=cb, progress_bar=False)

    fig, ax = plt.subplots(figsize=(7, 4))
    if cb.ep_returns:
        window = max(1, len(cb.ep_returns) // 10)
        smoothed = np.convolve(cb.ep_returns, np.ones(window) / window, mode="valid")
        ax.plot(cb.ep_steps[:len(smoothed)], smoothed, color="#0b6f64", linewidth=2,
                label=f"SAC (window={window})")
        ax.scatter(cb.ep_steps, cb.ep_returns, alpha=0.15, s=8, color="#69736e")
    ax.axhline(y=0, color="#9d650b", linestyle="--", alpha=0.5, label="Best possible (0)")
    ax.set_xlabel("Env Steps")
    ax.set_ylabel("Episode Return")
    ax.set_title("SAC (Stable-Baselines3) - Pendulum-v1")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(IMG_DIR / "sac_pendulum_curve.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {IMG_DIR / 'sac_pendulum_curve.png'}")


def plot_reward_shaping() -> None:
    data = json.loads((OUT_DIR / "reward_shaping.json").read_text())

    fig, ax = plt.subplots(figsize=(7, 4))
    colors = {"sparse": "#9d650b", "dense": "#5b4fa8", "shaped": "#0b6f64"}
    window = 15
    for kind in ["sparse", "dense", "shaped"]:
        curve = np.array(data[kind]["curve_seed0"])
        smoothed = np.convolve(curve, np.ones(window) / window, mode="valid")
        ax.plot(range(len(smoothed)), smoothed, color=colors[kind], linewidth=2,
                label=f"{kind} (window={window})")
    ax.set_xlabel("Episode")
    ax.set_ylabel("Success (1=reached goal)")
    ax.set_title("Reward Shaping Comparison - 1D GridWorld")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 1.05)
    plt.tight_layout()
    fig.savefig(IMG_DIR / "reward_shaping_curve.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {IMG_DIR / 'reward_shaping_curve.png'}")


def main() -> None:
    plot_reward_shaping()
    print("--- PPO CartPole ---")
    plot_ppo_cartpole()
    print("--- SAC Pendulum ---")
    plot_sac_pendulum()


if __name__ == "__main__":
    main()
