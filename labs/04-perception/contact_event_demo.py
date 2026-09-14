"""4.7 - Simulate a contact / slip event timeline for grasping.

Run:
    python labs/04-perception/contact_event_demo.py
"""
from __future__ import annotations

import csv
import os
from collections import Counter


RUN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "runs", "05-perception")
)
os.makedirs(RUN_DIR, exist_ok=True)


def classify_event(force_n: float, width_m: float, lift_progress_m: float) -> tuple[str, str | None]:
    if force_n < 0.10:
        return "no_contact", None
    if force_n < 0.75:
        return "contact_onset", None
    if lift_progress_m < -0.010 and force_n < 0.75:
        return "slip_detected", "slip_after_lift"
    return "stable_grasp", None


def main() -> None:
    rows: list[dict[str, float | str | None]] = []

    for step in range(50):
        t_ms = step * 20
        width_m = max(0.025, 0.100 - 0.0005 * t_ms)
        if t_ms < 120:
            phase = "close"
            force_n = max(0.0, (t_ms - 80) * 0.012)
            lift_progress_m = 0.0
        elif t_ms < 720:
            phase = "hold"
            force_n = 0.90
            lift_progress_m = 0.0
        else:
            phase = "lift"
            lift_progress_m = -0.00008 * (t_ms - 720)
            force_n = 0.90 if t_ms < 900 else 0.60

        event_type, failure_code = classify_event(force_n, width_m, lift_progress_m)
        if phase == "lift" and lift_progress_m < -0.010 and force_n < 0.75:
            event_type = "slip_detected"
            failure_code = "slip_after_lift"
        elif phase == "lift":
            event_type = "lift"

        rows.append(
            {
                "t_ms": t_ms,
                "phase": phase,
                "event_type": event_type,
                "force_n": round(force_n, 3),
                "width_m": round(width_m, 4),
                "lift_progress_m": round(lift_progress_m, 4),
                "failure_code": failure_code,
            }
        )

    out_path = os.path.join(RUN_DIR, "contact_events.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "t_ms",
                "phase",
                "event_type",
                "force_n",
                "width_m",
                "lift_progress_m",
                "failure_code",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'t_ms':>6s}  {'phase':12s} {'event_type':16s} {'force_N':>8s} {'width_m':>9s}   failure")
    print("-" * 76)
    for row in rows[:15]:
        failure = row["failure_code"] or ""
        print(
            f"{int(row['t_ms']):6d}  {str(row['phase']):12s} {str(row['event_type']):16s} "
            f"{float(row['force_n']):8.2f} {float(row['width_m']):9.4f}   {failure}"
        )

    stats = Counter(str(row["event_type"]) for row in rows)
    print("\nevent counts:")
    for key in ("no_contact", "contact_onset", "stable_grasp", "lift", "slip_detected"):
        if key in stats:
            print(f"  {key}: {stats[key]}")

    print(f"\nwrote {out_path}")
    assert any(row["event_type"] == "slip_detected" for row in rows), "slip event was not generated"
    print(">>> PASS: simulated grasp log contains contact, stable grasp, lift and slip events.")


if __name__ == "__main__":
    main()
