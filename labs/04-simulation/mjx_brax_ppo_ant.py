"""4.8 — Brax PPO on Ant (MJX backend).

Reproduces section/.../08-training-recipes/03-mjx-brax-pipeline.md:
  - Use Brax envs with backend="mjx"
  - Run PPO and log per-eval metrics via the training callback

Teaching defaults (1024 envs, 2M steps) run on a small GPU in a couple of
minutes as a smoke test. The committed log under runs/ was produced with the
"real" config used in the docs:
    BRAX_NUM_ENVS=4096 BRAX_TIMESTEPS=50000000 python labs/04-simulation/mjx_brax_ppo_ant.py

REQUIRES: NVIDIA GPU + jax + mujoco-mjx + brax (`pip install brax`).

Run:
    python labs/04-simulation/mjx_brax_ppo_ant.py

Outputs:
    runs/04-simulation/mjx_brax_ppo_ant.txt
    runs/04-simulation/mjx_brax_ppo_ant_metrics.json
    runs/04-simulation/mjx_brax_ppo_ant_policy.params
"""
from __future__ import annotations

import functools
import json
import os
import time
from pathlib import Path

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

try:
    import jax
except ImportError as exc:
    raise RuntimeError("jax missing; pip install 'jax[cuda12]'") from exc

try:
    from brax import envs
    from brax.training.agents.ppo import train as ppo
    from brax.io import model as brax_model
except ImportError as exc:
    raise RuntimeError("brax missing; pip install brax") from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

ENV_NAME = os.environ.get("BRAX_ENV", "ant")              # "ant" or "humanoid"
NUM_ENVS = int(os.environ.get("BRAX_NUM_ENVS", "1024"))   # 4096-8192 on big GPUs
NUM_TIMESTEPS = int(os.environ.get("BRAX_TIMESTEPS", "2000000"))  # smoke; 50M+ for real


def main() -> None:
    print(f"[info] JAX backend: {jax.default_backend()}")
    print(f"[info] JAX devices: {jax.devices()}")
    print(f"[info] Env: {ENV_NAME}, num_envs: {NUM_ENVS}, total steps: {NUM_TIMESTEPS:,}")

    env = envs.get_environment(env_name=ENV_NAME, backend="mjx")
    print(f"[env]  obs_size={env.observation_size}  action_size={env.action_size}")

    metrics_log: list[dict] = []

    def progress(num_steps: int, metrics: dict) -> None:
        snapshot = {"step": int(num_steps)}
        for k, v in metrics.items():
            try:
                snapshot[k] = float(v)
            except Exception:
                snapshot[k] = str(v)
        metrics_log.append(snapshot)
        reward = snapshot.get("eval/episode_reward", "n/a")
        print(f"  step={num_steps:>12,}  eval_reward={reward}")

    train_fn = functools.partial(
        ppo.train,
        num_timesteps=NUM_TIMESTEPS,
        num_evals=10,
        reward_scaling=0.1,
        episode_length=1000,
        normalize_observations=True,
        action_repeat=1,
        unroll_length=5,
        num_minibatches=32,
        num_updates_per_batch=4,
        discounting=0.97,
        learning_rate=3e-4,
        entropy_cost=1e-2,
        num_envs=NUM_ENVS,
        batch_size=1024,
        seed=0,
    )

    t0 = time.perf_counter()
    _make_inference_fn, params, _final_metrics = train_fn(environment=env, progress_fn=progress)
    elapsed = time.perf_counter() - t0
    print(f"\n[time] full training wall-clock = {elapsed:.1f} s ({elapsed/60:.1f} min)")

    brax_model.save_params(str(RUNS / "mjx_brax_ppo_ant_policy.params"), params)
    (RUNS / "mjx_brax_ppo_ant_metrics.json").write_text(json.dumps(metrics_log, indent=2))

    final = metrics_log[-1] if metrics_log else {}
    sps_vals = [m["training/sps"] for m in metrics_log if "training/sps" in m]
    steady_sps = max(sps_vals) if sps_vals else None
    summary = [
        f"JAX backend: {jax.default_backend()}",
        f"JAX devices: {[str(d) for d in jax.devices()]}",
        f"Env: {ENV_NAME}  (backend=mjx)",
        f"obs_size={env.observation_size}  action_size={env.action_size}",
        f"num_timesteps: {NUM_TIMESTEPS:,}  |  num_envs: {NUM_ENVS}",
        "",
        f"Wall-clock (incl. compile + eval): {elapsed:.1f} s  ({elapsed/60:.2f} min)",
        f"Overall throughput: {NUM_TIMESTEPS / elapsed:.0f} env-steps/s (incl. compile + eval)",
    ]
    if steady_sps:
        summary.append(f"Steady-state training throughput: {steady_sps:.0f} env-steps/s")
    summary += ["", "Final eval metrics:"]
    for k, v in final.items():
        summary.append(f"  {k}: {v}")
    (RUNS / "mjx_brax_ppo_ant.txt").write_text("\n".join(summary) + "\n")
    print(f"[write] {RUNS / 'mjx_brax_ppo_ant.txt'}")
    print(f"[write] {RUNS / 'mjx_brax_ppo_ant_metrics.json'}")


if __name__ == "__main__":
    main()
