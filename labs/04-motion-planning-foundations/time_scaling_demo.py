"""Multi-joint cubic time-scaling demo used by section 4.1.4.

The profile is deliberately simple and inspectable.  It demonstrates why all
joints need one shared duration and why velocity/acceleration must be checked.
Use a production library such as MoveIt TOTG or Ruckig for robot execution.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def minimum_cubic_duration(delta: np.ndarray, vmax: np.ndarray, amax: np.ndarray) -> float:
    # q(u)=q0+d(3u^2-2u^3), u=t/T
    # max |dq/dt| = 1.5 |d| / T; max |d2q/dt2| = 6 |d| / T^2
    velocity_time = 1.5 * np.abs(delta) / vmax
    acceleration_time = np.sqrt(6.0 * np.abs(delta) / amax)
    return float(np.max(np.maximum(velocity_time, acceleration_time)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dt", type=float, default=0.01)
    parser.add_argument("--speed-scale", type=float, default=0.6)
    parser.add_argument("--output", type=Path, default=Path("time_scaling.png"))
    args = parser.parse_args()
    if not 0.0 < args.speed_scale <= 1.0:
        raise ValueError("--speed-scale must be in (0, 1]")

    q0 = np.array([0.0, -0.7, 0.4])
    q1 = np.array([1.2, 0.4, -0.5])
    vmax = args.speed_scale * np.array([1.2, 1.0, 1.4])
    amax = args.speed_scale * np.array([2.2, 1.8, 2.4])
    delta = q1 - q0
    duration = minimum_cubic_duration(delta, vmax, amax)
    time = np.arange(0.0, duration + args.dt, args.dt)
    time[-1] = duration
    u = np.clip(time / duration, 0.0, 1.0)[:, None]

    q = q0 + delta * (3.0 * u**2 - 2.0 * u**3)
    qd = delta * (6.0 * u - 6.0 * u**2) / duration
    qdd = delta * (6.0 - 12.0 * u) / duration**2

    print(f"duration_s={duration:.4f}")
    print(f"samples={len(time)}")
    print(f"max_velocity={np.max(np.abs(qd), axis=0)}")
    print(f"max_acceleration={np.max(np.abs(qdd), axis=0)}")
    print(f"velocity_limits={vmax}")
    print(f"acceleration_limits={amax}")

    fig, axes = plt.subplots(3, 1, figsize=(9.0, 8.0), sharex=True, constrained_layout=True)
    for joint in range(q.shape[1]):
        axes[0].plot(time, q[:, joint], label=f"joint {joint + 1}")
        axes[1].plot(time, qd[:, joint])
        axes[2].plot(time, qdd[:, joint])
        axes[1].axhline(vmax[joint], color="#aab6bf", linewidth=0.7)
        axes[1].axhline(-vmax[joint], color="#aab6bf", linewidth=0.7)
        axes[2].axhline(amax[joint], color="#aab6bf", linewidth=0.7)
        axes[2].axhline(-amax[joint], color="#aab6bf", linewidth=0.7)
    axes[0].set_ylabel("position [rad]")
    axes[1].set_ylabel("velocity [rad/s]")
    axes[2].set_ylabel("acceleration [rad/s²]")
    axes[2].set_xlabel("time [s]")
    axes[0].legend(ncol=3)
    axes[0].set_title("Synchronized cubic time scaling")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=170)
    print(f"saved={args.output.resolve()}")


if __name__ == "__main__":
    main()
