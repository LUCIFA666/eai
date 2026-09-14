"""7.4 - Generate behavior-cloning demos from a scripted PD pendulum.

We reuse the pendulum dynamics from ``labs/03-robotics/pd_control.py`` and treat
its well-tuned PD controller as a *scripted expert*. We then roll out 50 episodes
with varied step targets and random initial states, save the resulting
``(obs, action)`` pairs to ``runs/07-data/scripted_demos.npz``, and print a few
dataset statistics. This dataset is consumed by ``bc_pendulum.py``.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/07-data/scripted_pendulum_demos.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

GRAVITY = 9.81
MASS = 1.0
LENGTH = 0.5
DAMPING = 0.10
DT = 0.005
TFINAL = 3.0
KP, KD = 15.0, 0.6
TAU_LIMIT = 3.0


def step(theta: float, omega: float, tau: float) -> tuple[float, float]:
    moi = MASS * LENGTH * LENGTH
    grav = -MASS * GRAVITY * LENGTH * math.sin(theta)
    omega_next = omega + DT * (tau + grav - DAMPING * omega) / moi
    theta_next = theta + DT * omega_next
    return theta_next, omega_next


def rollout(target: float, theta0: float, omega0: float) -> dict:
    n = int(TFINAL / DT)
    obs = np.zeros((n, 3), dtype=np.float32)  # (theta, omega, target)
    act = np.zeros((n, 1), dtype=np.float32)  # torque
    theta, omega = theta0, omega0
    for i in range(n):
        err = target - theta
        tau = float(np.clip(KP * err - KD * omega, -TAU_LIMIT, TAU_LIMIT))
        obs[i] = (theta, omega, target)
        act[i] = tau
        theta, omega = step(theta, omega, tau)
    final_err = theta - target
    return {
        "obs": obs,
        "act": act,
        "target": target,
        "final_err": final_err,
        "success": abs(final_err) < math.radians(2.0),
    }


def main() -> None:
    rng = np.random.default_rng(seed=42)
    n_episodes = 50
    episodes = []
    for k in range(n_episodes):
        target = rng.uniform(-math.radians(80), math.radians(80))
        theta0 = rng.uniform(-math.radians(20), math.radians(20))
        omega0 = rng.uniform(-0.5, 0.5)
        ep = rollout(target, theta0, omega0)
        ep["episode_index"] = k
        episodes.append(ep)

    obs = np.concatenate([e["obs"] for e in episodes], axis=0)
    act = np.concatenate([e["act"] for e in episodes], axis=0)
    ep_idx = np.concatenate(
        [np.full(len(e["obs"]), e["episode_index"], dtype=np.int32) for e in episodes]
    )
    successes = np.array([e["success"] for e in episodes], dtype=bool)
    targets = np.array([e["target"] for e in episodes], dtype=np.float32)

    out = Path("runs/07-data/scripted_demos.npz")
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out,
        obs=obs,
        act=act,
        episode_index=ep_idx,
        success=successes,
        target=targets,
        dt=DT,
        kp=KP,
        kd=KD,
    )

    print(f"episodes      : {n_episodes}")
    print(f"timesteps/ep  : {len(episodes[0]['obs'])}")
    print(f"obs shape     : {obs.shape}  (theta, omega, target)")
    print(f"act shape     : {act.shape}  (torque, Nm)")
    print(f"success rate  : {successes.mean():.2%}")
    print(f"|final_err| mean(deg): {np.mean([abs(math.degrees(e['final_err'])) for e in episodes]):.2f}")
    print(f"action range  : [{act.min():+.3f}, {act.max():+.3f}] Nm")
    print(f"wrote {out}  ({out.stat().st_size/1024:.1f} KiB)")


if __name__ == "__main__":
    main()
