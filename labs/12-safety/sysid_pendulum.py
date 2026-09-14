"""12.2 — System identification: fit (length, damping) from a noisy trajectory.

A pendulum with TRUE = (mass=1.0, length=0.55, damping=0.18, g=9.81)
is driven by a chirp torque, sampled at 50 Hz, and observed with
~0.6 deg noise.  We recover (length, damping) via coarse grid +
local refinement (no scipy needed).

Run:
    python labs/12-safety/sysid_pendulum.py
Outputs:
    runs/12-safety/sysid_pendulum.json
    runs/12-safety/sysid_trace.csv
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

TRUE = dict(mass=1.0, length=0.55, damping=0.18, gravity=9.81)
DT = 0.02
T_FINAL = 4.0
NOISE_STD = math.radians(0.6)    # ~0.6 deg sensor noise
N_STEPS = int(T_FINAL / DT)


def torque_schedule(t: float) -> float:
    # A small chirp so several frequencies excite the dynamics.
    f = 0.5 + 0.6 * t          # Hz, ramps from 0.5 to ~2.9
    return 0.6 * math.sin(2 * math.pi * f * t)


def simulate(mass: float, length: float, damping: float, gravity: float = 9.81) -> np.ndarray:
    theta = 0.0; omega = 0.0; t = 0.0
    moi = mass * length * length
    out = np.empty((N_STEPS, 4), dtype=np.float64)
    for i in range(N_STEPS):
        tau = torque_schedule(t)
        grav = -mass * gravity * length * math.sin(theta)
        omega += DT * (tau + grav - damping * omega) / moi
        theta += DT * omega
        out[i] = (t, theta, omega, tau)
        t += DT
    return out


def residual(meas_theta: np.ndarray, fit_theta: np.ndarray) -> float:
    return float(np.sqrt(np.mean((meas_theta - fit_theta) ** 2)))


def grid_search(meas_theta: np.ndarray, length_grid: np.ndarray,
                damping_grid: np.ndarray, mass: float) -> tuple[float, float, float]:
    best = (float("inf"), 0.0, 0.0)
    for L in length_grid:
        for c in damping_grid:
            sim = simulate(mass=mass, length=float(L), damping=float(c))
            r = residual(meas_theta, sim[:, 1])
            if r < best[0]:
                best = (r, float(L), float(c))
    return best  # (residual, L, c)


def main() -> None:
    out_dir = Path("runs/12-safety"); out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)

    truth = simulate(**TRUE)
    meas_theta = truth[:, 1] + rng.normal(0.0, NOISE_STD, size=N_STEPS)

    # Stage 1: coarse grid.  Mass is assumed known (one common assumption
    # in robotics: payload weighed before run).
    coarse_L = np.linspace(0.30, 0.80, 26)            # 0.02 spacing
    coarse_c = np.linspace(0.00, 0.40, 21)            # 0.02 spacing
    r1, L1, c1 = grid_search(meas_theta, coarse_L, coarse_c, mass=TRUE["mass"])

    # Stage 2: local refinement around the coarse winner.
    fine_L = np.linspace(L1 - 0.025, L1 + 0.025, 21)
    fine_c = np.linspace(max(0.0, c1 - 0.025), c1 + 0.025, 21)
    r2, L2, c2 = grid_search(meas_theta, fine_L, fine_c, mass=TRUE["mass"])

    fit_trace = simulate(mass=TRUE["mass"], length=L2, damping=c2)

    report = {
        "truth": TRUE, "noise_std_deg": math.degrees(NOISE_STD),
        "fit": {"length": L2, "damping": c2, "mass": TRUE["mass"],
                 "residual_rad": r2, "residual_deg": math.degrees(r2)},
        "errors": {"length_abs": abs(L2 - TRUE["length"]),
                    "damping_abs": abs(c2 - TRUE["damping"]),
                    "length_rel_pct": 100 * abs(L2 - TRUE["length"]) / TRUE["length"],
                    "damping_rel_pct": 100 * abs(c2 - TRUE["damping"]) / TRUE["damping"]},
        "coarse_stage": {"residual_rad": r1, "length": L1, "damping": c1},
    }
    (out_dir / "sysid_pendulum.json").write_text(json.dumps(report, indent=2) + "\n")

    with (out_dir / "sysid_trace.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(("t", "truth_theta", "meas_theta", "fit_theta"))
        for i in range(N_STEPS):
            w.writerow((round(truth[i, 0], 4), round(truth[i, 1], 6),
                        round(meas_theta[i], 6), round(fit_trace[i, 1], 6)))

    print(f"truth          : length={TRUE['length']:.4f}  damping={TRUE['damping']:.4f}")
    print(f"coarse fit (r={r1:.4f}): length={L1:.4f}  damping={c1:.4f}")
    print(f"fine fit   (r={r2:.4f}): length={L2:.4f}  damping={c2:.4f}")
    print(f"abs error: dL={report['errors']['length_abs']:.4f}m "
          f"({report['errors']['length_rel_pct']:.2f}%), "
          f"dc={report['errors']['damping_abs']:.4f} "
          f"({report['errors']['damping_rel_pct']:.2f}%)")
    print(f"\nwrote {out_dir / 'sysid_pendulum.json'} and sysid_trace.csv")


if __name__ == "__main__":
    main()
