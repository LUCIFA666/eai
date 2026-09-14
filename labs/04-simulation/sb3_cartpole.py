"""4.8 — SB3 PPO on dm_control cartpole via shimmy.

Backs the "CartPole + SB3" recipe: the correct MuJoCo-backed path is
dm_control's cartpole swingup wrapped with shimmy.DmControlCompatibilityV0
(not gym.make("CartPole-v1"), which is the classic discrete, non-MuJoCo env).
Trains a short smoke run and evaluates.

Run:
    python labs/04-simulation/sb3_cartpole.py

Outputs:
    runs/04-simulation/sb3_cartpole.txt
    runs/04-simulation/sb3_cartpole_ppo.zip   (trained policy)
"""
from __future__ import annotations

from pathlib import Path

try:
    from dm_control import suite
except ImportError as exc:
    raise RuntimeError("dm_control missing; pip install dm_control") from exc

try:
    from shimmy import DmControlCompatibilityV0
except ImportError as exc:
    raise RuntimeError("shimmy missing; pip install shimmy") from exc

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.evaluation import evaluate_policy
except ImportError as exc:
    raise RuntimeError("stable-baselines3 missing; pip install stable-baselines3") from exc

from gymnasium.wrappers import FlattenObservation

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

TOTAL_TIMESTEPS = 10_000  # smoke test; bump to 200_000 to actually learn swingup


def main() -> None:
    dm_env = suite.load("cartpole", "swingup", task_kwargs={"random": 0})
    env = DmControlCompatibilityV0(dm_env, render_mode="rgb_array")
    env = FlattenObservation(env)   # dict obs -> Box, for MlpPolicy

    print(f"action_space: {env.action_space}")
    print(f"obs_space:    {env.observation_space}")

    model = PPO("MlpPolicy", env, verbose=1, device="cpu")
    model.learn(total_timesteps=TOTAL_TIMESTEPS)
    model.save(str(RUNS / "sb3_cartpole_ppo"))

    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
    print(f"\nEval: mean_reward={mean_reward:.2f} +/- {std_reward:.2f}")

    (RUNS / "sb3_cartpole.txt").write_text(
        "env: dm_control cartpole swingup (via shimmy.DmControlCompatibilityV0)\n"
        f"action_space: {env.action_space}\n"
        f"obs_space: {env.observation_space}\n"
        "algorithm: PPO (MlpPolicy, cpu)\n"
        f"total_timesteps: {TOTAL_TIMESTEPS}\n"
        f"eval_mean_reward: {mean_reward:.2f}\n"
        f"eval_std_reward: {std_reward:.2f}\n"
    )
    print("\n[OK] SB3 + dm_control cartpole via shimmy trains and evaluates.")


if __name__ == "__main__":
    main()
