"""12.1 — Domain randomization on a numpy pendulum.

Sample mass, length, damping, gravity around nominal values, run a
gravity-compensated PD controller tuned at nominal, and report the
success rate distribution.  Shows the classic DR effect: success
drops as the randomization range grows.

Run:
    python labs/12-safety/domain_randomization.py
Outputs:
    runs/12-safety/domain_randomization.json
    runs/12-safety/domain_randomization.csv
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

DT = 0.02         # 50 Hz
T_FINAL = 3.0
TARGET = math.radians(45.0)
SETTLE_BAND = math.radians(2.0)   # tight: within 2 deg of target
SETTLE_FRAC = 0.6                  # must be inside band for last 60% of episode

NOMINAL = dict(mass=1.0, length=0.5, damping=0.10, gravity=9.81)
KP, KD = 30.0, 2.0
TORQUE_LIMIT = 8.0
N_TRIALS = 200
# Feed-forward uses NOMINAL m, g, L. When real params jitter, the FF
# is wrong by ~the parameter mismatch; this is exactly what DR is meant
# to fix on the *policy* side.
FF_NOMINAL = NOMINAL["mass"] * NOMINAL["gravity"] * NOMINAL["length"]


def simulate(mass: float, length: float, damping: float, gravity: float,
             obs_noise: float = 0.0, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng if rng is not None else np.random.default_rng(0)
    theta = 0.0; omega = 0.0; t = 0.0
    moi = mass * length * length
    rows = []
    while t < T_FINAL:
        theta_meas = theta + (rng.normal(0.0, obs_noise) if obs_noise > 0 else 0.0)
        err = TARGET - theta_meas
        ff = FF_NOMINAL * math.sin(theta_meas)        # gravity FF at NOMINAL
        tau = float(np.clip(KP * err - KD * omega + ff, -TORQUE_LIMIT, TORQUE_LIMIT))
        grav = -mass * gravity * length * math.sin(theta)
        omega += DT * (tau + grav - damping * omega) / moi
        theta += DT * omega
        rows.append((t, theta, omega, tau))
        t += DT
    return np.array(rows)


def episode_success(trace: np.ndarray) -> bool:
    theta = trace[:, 1]
    n = theta.size
    cutoff = int(n * (1.0 - SETTLE_FRAC))
    return bool(np.all(np.abs(theta[cutoff:] - TARGET) < SETTLE_BAND))


def sample_params(rng: np.random.Generator, scale: float) -> dict[str, float]:
    """Uniform jitter around nominal: scale=0 -> nominal only."""
    return {"mass":    NOMINAL["mass"]    * (1.0 + rng.uniform(-0.4, 0.4) * scale),
            "length":  NOMINAL["length"]  * (1.0 + rng.uniform(-0.2, 0.2) * scale),
            "damping": max(0.0, NOMINAL["damping"] + rng.uniform(-0.08, 0.20) * scale),
            "gravity": NOMINAL["gravity"] * (1.0 + rng.uniform(-0.10, 0.10) * scale)}


def main() -> None:
    out_dir = Path("runs/12-safety"); out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)

    report = {"trials_per_regime": N_TRIALS, "regimes": {}}
    csv_rows = [("regime", "trial", "mass", "length", "damping", "gravity",
                 "final_theta_deg", "peak_torque", "success")]

    for regime, dr_scale, obs_noise in [
        ("nominal_only", 0.0, 0.0),
        ("mild_dr", 0.5, 0.005),
        ("aggressive_dr", 1.0, 0.02),
    ]:
        succ = 0
        for i in range(N_TRIALS):
            p = sample_params(rng, dr_scale)
            tr = simulate(**p, obs_noise=obs_noise, rng=rng)
            ok = episode_success(tr)
            succ += int(ok)
            csv_rows.append((regime, i, round(p["mass"], 4), round(p["length"], 4),
                             round(p["damping"], 4), round(p["gravity"], 4),
                             round(math.degrees(tr[-1, 1]), 3),
                             round(float(np.max(np.abs(tr[:, 3]))), 3), int(ok)))
        rate = succ / N_TRIALS
        # 95% Wilson CI for a binomial proportion (no scipy)
        z = 1.96; denom = 1 + z * z / N_TRIALS
        center = (rate + z * z / (2 * N_TRIALS)) / denom
        half = z * math.sqrt(rate * (1 - rate) / N_TRIALS + z * z / (4 * N_TRIALS ** 2)) / denom
        report["regimes"][regime] = {"success_rate": rate, "dr_scale": dr_scale,
            "ci95_lo": max(0.0, center - half), "ci95_hi": min(1.0, center + half),
            "obs_noise_rad": obs_noise}

    (out_dir / "domain_randomization.json").write_text(json.dumps(report, indent=2) + "\n")
    with (out_dir / "domain_randomization.csv").open("w", newline="") as f:
        csv.writer(f).writerows(csv_rows)

    print(f"controller: kp={KP}, kd={KD}, torque_limit={TORQUE_LIMIT}")
    print(f"{'regime':>18}  {'n':>4}  {'success':>8}  {'ci95':>16}  dr_scale  obs_noise")
    for r, d in report["regimes"].items():
        print(f"{r:>18}  {N_TRIALS:>4d}  {d['success_rate']:>8.3f}  "
              f"[{d['ci95_lo']:.3f},{d['ci95_hi']:.3f}]  "
              f"{d['dr_scale']:>8.2f}  {d['obs_noise_rad']:>8.4f}")
    print(f"\nwrote {out_dir / 'domain_randomization.json'} and .csv")


if __name__ == "__main__":
    main()
