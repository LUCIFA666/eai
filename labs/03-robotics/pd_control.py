"""3.6 — PD/PID control on a single-joint pendulum (no MuJoCo needed).

This script integrates a damped pendulum with gravity using
semi-implicit Euler and applies a PD controller to track a step
target.  We deliberately keep it under 100 lines so learners can
read it end-to-end.

Run:
    python labs/03-robotics/pd_control.py

Outputs:
- prints summary metrics (rise time, overshoot, settling time)
- writes ``runs/03-robotics/pd_curve.csv`` with the trace
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

GRAVITY = 9.81
MASS = 1.0
LENGTH = 0.5
DAMPING = 0.10  # small viscous friction
DT = 0.005     # 200 Hz control loop
TFINAL = 4.0   # seconds


def step(theta: float, omega: float, tau: float) -> tuple[float, float]:
    """Semi-implicit Euler step of a single-link pendulum."""
    moi = MASS * LENGTH * LENGTH
    grav = -MASS * GRAVITY * LENGTH * math.sin(theta)
    omega_next = omega + DT * (tau + grav - DAMPING * omega) / moi
    theta_next = theta + DT * omega_next
    return theta_next, omega_next


def simulate(kp: float, kd: float, target: float) -> np.ndarray:
    t = 0.0
    theta = 0.0
    omega = 0.0
    rows = []
    while t < TFINAL:
        err = target - theta
        tau = kp * err - kd * omega
        # respect a torque limit so the demo also teaches saturation.
        tau = max(-3.0, min(3.0, tau))
        theta, omega = step(theta, omega, tau)
        rows.append((t, target, theta, err, tau))
        t += DT
    return np.array(rows)


def metrics(trace: np.ndarray) -> dict[str, float]:
    t, target, theta, err, _ = trace.T
    final = target[-1]
    rise_idx = np.argmax(theta >= 0.9 * final)
    rise_time = float(t[rise_idx]) if theta[rise_idx] >= 0.9 * final else float("nan")
    overshoot = float((theta.max() - final) / final * 100.0)
    band = 0.02 * abs(final)
    settled = np.where(np.abs(theta - final) < band)[0]
    if len(settled) > 0:
        # first index after which it stays within band until end
        settling_time = float(t[settled[0]])
        for idx in settled:
            if np.all(np.abs(theta[idx:] - final) < band):
                settling_time = float(t[idx])
                break
    else:
        settling_time = float("nan")
    return {
        "rise_time_s": rise_time,
        "overshoot_pct": overshoot,
        "settling_time_s": settling_time,
        "final_err_rad": float(theta[-1] - final),
        "peak_torque_Nm": float(np.max(np.abs(trace[:, 4]))),
    }


def main() -> None:
    target = math.radians(45)
    out_path = Path("runs/03-robotics/pd_curve.csv")
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        import os, tempfile
        out_path = Path(os.environ.get("TMPDIR", tempfile.gettempdir())) / "pd_curve.csv"
        print(f"[warn] runs/ is read-only; writing CSV to {out_path}")

    summary = []
    for kp, kd in [(5.0, 0.1), (15.0, 0.6), (30.0, 0.2)]:
        trace = simulate(kp=kp, kd=kd, target=target)
        m = metrics(trace)
        m["kp"] = kp
        m["kd"] = kd
        summary.append(m)
        # save the last (well-tuned) trace
        if (kp, kd) == (15.0, 0.6):
            with out_path.open("w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["t", "target", "theta", "err", "tau"])
                w.writerows(trace.tolist())

    print(f"target = {math.degrees(target):.1f} deg")
    print(f"{'kp':>6} {'kd':>6} {'rise(s)':>8} {'OS%':>8} {'settle(s)':>10} {'final_err(rad)':>16} {'peak_tau':>10}")
    for m in summary:
        print(
            f"{m['kp']:>6.1f} {m['kd']:>6.1f} {m['rise_time_s']:>8.3f} "
            f"{m['overshoot_pct']:>8.2f} {m['settling_time_s']:>10.3f} "
            f"{m['final_err_rad']:>16.4e} {m['peak_torque_Nm']:>10.3f}"
        )
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
