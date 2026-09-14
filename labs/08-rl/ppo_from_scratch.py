"""9.2 - Minimal PPO from scratch using only PyTorch + Gymnasium.

No external RL library — every component (rollout buffer, GAE, clipped
surrogate loss, value loss, entropy bonus) is implemented here so you
can read the full algorithm in < 200 lines.

Trains on CartPole-v1 and saves a training curve PNG + metrics JSON.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/08-rl/ppo_from_scratch.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import gymnasium as gym
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical

# ---------------------------------------------------------------------------
# Hyperparameters
# ---------------------------------------------------------------------------
ENV_ID = "CartPole-v1"
SEED = 42
TOTAL_TIMESTEPS = 80_000
N_ENVS = 4
N_STEPS = 128          # rollout length per env per update
BATCH_SIZE = 64
N_EPOCHS = 4           # PPO epochs per update
GAMMA = 0.99
GAE_LAMBDA = 0.95
CLIP_EPS = 0.2
LR = 3e-4
ENT_COEF = 0.0
VF_COEF = 0.5
MAX_GRAD_NORM = 0.5

OUT_DIR = Path("runs/08-rl")
IMG_DIR = Path("section/09-reinforcement-learning-for-robotics")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Actor-Critic network
# ---------------------------------------------------------------------------
def layer_init(layer: nn.Linear, std: float = np.sqrt(2), bias: float = 0.0):
    nn.init.orthogonal_(layer.weight, std)
    nn.init.constant_(layer.bias, bias)
    return layer


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, act_dim: int):
        super().__init__()
        self.actor = nn.Sequential(
            layer_init(nn.Linear(obs_dim, 64)), nn.Tanh(),
            layer_init(nn.Linear(64, 64)), nn.Tanh(),
            layer_init(nn.Linear(64, act_dim), std=0.01),
        )
        self.critic = nn.Sequential(
            layer_init(nn.Linear(obs_dim, 64)), nn.Tanh(),
            layer_init(nn.Linear(64, 64)), nn.Tanh(),
            layer_init(nn.Linear(64, 1), std=1.0),
        )

    def forward(self, x: torch.Tensor):
        return self.actor(x), self.critic(x).squeeze(-1)

    def get_action_and_value(self, obs: torch.Tensor):
        logits, value = self(obs)
        dist = Categorical(logits=logits)
        action = dist.sample()
        return action, dist.log_prob(action), dist.entropy(), value

    def evaluate(self, obs: torch.Tensor, actions: torch.Tensor):
        logits, value = self(obs)
        dist = Categorical(logits=logits)
        return dist.log_prob(actions), dist.entropy(), value


# ---------------------------------------------------------------------------
# Vectorized env helper (sync)
# ---------------------------------------------------------------------------
def make_envs(env_id: str, n: int, seed: int):
    def _make(i):
        def _init():
            e = gym.make(env_id)
            e.reset(seed=seed + i)
            return e
        return _init
    return gym.vector.SyncVectorEnv([_make(i) for i in range(n)])


# ---------------------------------------------------------------------------
# GAE computation
# ---------------------------------------------------------------------------
def compute_gae(
    rewards: np.ndarray,      # (n_steps, n_envs)
    values: np.ndarray,       # (n_steps, n_envs)
    dones: np.ndarray,        # (n_steps, n_envs)
    last_value: np.ndarray,   # (n_envs,)
) -> tuple[np.ndarray, np.ndarray]:
    n_steps, n_envs = rewards.shape
    advantages = np.zeros_like(rewards)
    last_gae = np.zeros(n_envs)
    for t in reversed(range(n_steps)):
        next_val = last_value if t == n_steps - 1 else values[t + 1]
        next_non_terminal = 1.0 - dones[t]
        delta = rewards[t] + GAMMA * next_val * next_non_terminal - values[t]
        last_gae = delta + GAMMA * GAE_LAMBDA * next_non_terminal * last_gae
        advantages[t] = last_gae
    returns = advantages + values
    return advantages, returns


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------
def train():
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    envs = make_envs(ENV_ID, N_ENVS, SEED)
    obs_dim = envs.single_observation_space.shape[0]
    act_dim = envs.single_action_space.n

    agent = ActorCritic(obs_dim, act_dim)
    optimizer = torch.optim.Adam(agent.parameters(), lr=LR, eps=1e-5)

    obs, _ = envs.reset(seed=SEED)
    global_step = 0
    num_updates = TOTAL_TIMESTEPS // (N_STEPS * N_ENVS)

    episode_returns: list[float] = []
    episode_steps: list[int] = []
    running_returns = np.zeros(N_ENVS)
    running_lengths = np.zeros(N_ENVS, dtype=int)

    update_metrics: list[dict] = []
    t0 = time.time()

    for update in range(num_updates):
        # -- Rollout phase --
        b_obs = np.zeros((N_STEPS, N_ENVS, obs_dim), dtype=np.float32)
        b_actions = np.zeros((N_STEPS, N_ENVS), dtype=np.int64)
        b_logprobs = np.zeros((N_STEPS, N_ENVS), dtype=np.float32)
        b_rewards = np.zeros((N_STEPS, N_ENVS), dtype=np.float32)
        b_dones = np.zeros((N_STEPS, N_ENVS), dtype=np.float32)
        b_values = np.zeros((N_STEPS, N_ENVS), dtype=np.float32)

        for step in range(N_STEPS):
            global_step += N_ENVS
            b_obs[step] = obs

            with torch.no_grad():
                obs_t = torch.as_tensor(obs, dtype=torch.float32)
                action, logprob, _, value = agent.get_action_and_value(obs_t)

            b_actions[step] = action.numpy()
            b_logprobs[step] = logprob.numpy()
            b_values[step] = value.numpy()

            obs, reward, terminated, truncated, infos = envs.step(action.numpy())
            done = np.logical_or(terminated, truncated)
            b_rewards[step] = reward
            b_dones[step] = done.astype(np.float32)

            running_returns += reward
            running_lengths += 1
            for i in range(N_ENVS):
                if done[i]:
                    episode_returns.append(float(running_returns[i]))
                    episode_steps.append(global_step)
                    running_returns[i] = 0.0
                    running_lengths[i] = 0

        # -- GAE --
        with torch.no_grad():
            last_val = agent(torch.as_tensor(obs, dtype=torch.float32))[1].numpy()
        advantages, returns = compute_gae(b_rewards, b_values, b_dones, last_val)

        # -- Flatten batch --
        total = N_STEPS * N_ENVS
        flat_obs = torch.as_tensor(b_obs.reshape(total, obs_dim))
        flat_act = torch.as_tensor(b_actions.reshape(total))
        flat_logp = torch.as_tensor(b_logprobs.reshape(total))
        flat_adv = torch.as_tensor(advantages.reshape(total))
        flat_ret = torch.as_tensor(returns.reshape(total))

        # Normalize advantages
        flat_adv = (flat_adv - flat_adv.mean()) / (flat_adv.std() + 1e-8)

        # -- PPO update epochs --
        indices = np.arange(total)
        pg_losses, v_losses, ent_losses = [], [], []

        for _ in range(N_EPOCHS):
            np.random.shuffle(indices)
            for start in range(0, total, BATCH_SIZE):
                end = start + BATCH_SIZE
                idx = indices[start:end]

                new_logp, entropy, new_val = agent.evaluate(flat_obs[idx], flat_act[idx])

                # Policy loss (clipped surrogate)
                log_ratio = new_logp - flat_logp[idx]
                ratio = log_ratio.exp()
                pg_loss1 = -flat_adv[idx] * ratio
                pg_loss2 = -flat_adv[idx] * torch.clamp(ratio, 1 - CLIP_EPS, 1 + CLIP_EPS)
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()

                # Value loss
                v_loss = 0.5 * ((new_val - flat_ret[idx]) ** 2).mean()

                # Entropy bonus
                ent_loss = entropy.mean()

                loss = pg_loss + VF_COEF * v_loss - ENT_COEF * ent_loss

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(agent.parameters(), MAX_GRAD_NORM)
                optimizer.step()

                pg_losses.append(pg_loss.item())
                v_losses.append(v_loss.item())
                ent_losses.append(ent_loss.item())

        update_metrics.append({
            "update": update,
            "global_step": global_step,
            "pg_loss": float(np.mean(pg_losses)),
            "v_loss": float(np.mean(v_losses)),
            "entropy": float(np.mean(ent_losses)),
        })

    wall = time.time() - t0
    envs.close()

    # -- Evaluate --
    eval_env = gym.make(ENV_ID)
    eval_returns = []
    for ep in range(20):
        obs_e, _ = eval_env.reset(seed=SEED + 1000 + ep)
        total_r = 0.0
        while True:
            with torch.no_grad():
                logits, _ = agent(torch.as_tensor(obs_e, dtype=torch.float32).unsqueeze(0))
                action = logits.argmax(dim=-1).item()
            obs_e, r, term, trunc, _ = eval_env.step(action)
            total_r += r
            if term or trunc:
                break
        eval_returns.append(total_r)
    eval_env.close()

    # -- Save metrics --
    metrics = {
        "status": "ok",
        "env": ENV_ID,
        "algo": "PPO (from scratch)",
        "total_timesteps": TOTAL_TIMESTEPS,
        "n_envs": N_ENVS,
        "eval_return_mean": float(np.mean(eval_returns)),
        "eval_return_std": float(np.std(eval_returns)),
        "wall_clock_s": round(wall, 2),
        "steps_per_sec": int(TOTAL_TIMESTEPS / wall),
        "episode_returns": episode_returns,
        "episode_steps": episode_steps,
        "update_metrics": update_metrics,
    }
    out = OUT_DIR / "ppo_scratch_metrics.json"
    out.write_text(json.dumps(metrics, indent=2))
    print(f"eval return     : {np.mean(eval_returns):.1f} +/- {np.std(eval_returns):.1f}")
    print(f"wall clock      : {wall:.1f}s  ({int(TOTAL_TIMESTEPS / wall)} steps/s)")
    print(f"wrote {out}")

    # -- Plot training curve --
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Smoothed episode returns
    window = max(1, len(episode_returns) // 20)
    smoothed = np.convolve(episode_returns, np.ones(window) / window, mode="valid")
    ax1.plot(episode_steps[:len(smoothed)], smoothed, color="#0b6f64", linewidth=2,
             label=f"Moving avg (window={window})")
    ax1.scatter(episode_steps, episode_returns, alpha=0.15, s=8, color="#69736e")
    ax1.set_xlabel("Env Steps")
    ax1.set_ylabel("Episode Return")
    ax1.set_title("PPO From Scratch - CartPole-v1")
    ax1.axhline(y=500, color="#9d650b", linestyle="--", alpha=0.7, label="Optimal (500)")
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Loss curves
    steps = [m["global_step"] for m in update_metrics]
    ax2.plot(steps, [m["pg_loss"] for m in update_metrics],
             label="Policy Loss", color="#0b6f64")
    ax2.plot(steps, [m["v_loss"] for m in update_metrics],
             label="Value Loss", color="#9d650b")
    ax2_twin = ax2.twinx()
    ax2_twin.plot(steps, [m["entropy"] for m in update_metrics],
                  label="Entropy", color="#5b4fa8", linestyle="--")
    ax2.set_xlabel("Env Steps")
    ax2.set_ylabel("Loss")
    ax2_twin.set_ylabel("Entropy")
    ax2.set_title("PPO Loss Curves")
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    img_path = IMG_DIR / "ppo_scratch_curve.png"
    fig.savefig(img_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {img_path}")
    return metrics


if __name__ == "__main__":
    train()
