"""3.3-3.4 — Two-link planar arm forward and inverse kinematics.

Goal: build the simplest possible arm that still shows reachability,
multiple IK branches, and singular configurations.  Pure numpy, no
simulation, no GPU.

Run:
    python labs/03-robotics/two_link_fk_ik.py

Reproducible: seed 0 is used for the random IK targets.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

L1 = 0.40  # length of link 1 in meters
L2 = 0.30  # length of link 2 in meters


def fk(q: np.ndarray) -> np.ndarray:
    """Forward kinematics: joint angles ``q = [q1, q2]`` to end-effector ``(x, y)``."""
    q1, q2 = q
    x = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
    y = L1 * math.sin(q1) + L2 * math.sin(q1 + q2)
    return np.array([x, y])


def jacobian(q: np.ndarray) -> np.ndarray:
    """2x2 analytic Jacobian d(x, y) / d(q1, q2)."""
    q1, q2 = q
    j11 = -L1 * math.sin(q1) - L2 * math.sin(q1 + q2)
    j12 = -L2 * math.sin(q1 + q2)
    j21 = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
    j22 = L2 * math.cos(q1 + q2)
    return np.array([[j11, j12], [j21, j22]])


def ik_analytic(target: np.ndarray, elbow: str = "up") -> np.ndarray | None:
    """Closed-form IK; returns None if the target is out of reach."""
    x, y = target
    r2 = x * x + y * y
    cos_q2 = (r2 - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    if cos_q2 < -1.0 - 1e-9 or cos_q2 > 1.0 + 1e-9:
        return None
    cos_q2 = float(np.clip(cos_q2, -1.0, 1.0))
    sin_q2 = math.sqrt(max(0.0, 1.0 - cos_q2 * cos_q2))
    if elbow == "down":
        sin_q2 = -sin_q2
    q2 = math.atan2(sin_q2, cos_q2)
    k1 = L1 + L2 * cos_q2
    k2 = L2 * sin_q2
    q1 = math.atan2(y, x) - math.atan2(k2, k1)
    return np.array([q1, q2])


@dataclass
class IKReport:
    target: np.ndarray
    joints: np.ndarray | None
    achieved: np.ndarray | None
    err: float | None
    note: str


def evaluate_targets(targets: np.ndarray) -> list[IKReport]:
    reports = []
    for t in targets:
        q = ik_analytic(t, elbow="up")
        if q is None:
            reports.append(IKReport(t, None, None, None, "unreachable"))
            continue
        achieved = fk(q)
        err = float(np.linalg.norm(achieved - t))
        # singularity test: |J| close to zero means we are at/near the
        # fully-extended or fully-folded configuration.
        det = float(np.linalg.det(jacobian(q)))
        note = "ok"
        if abs(det) < 1e-4:
            note = "near-singular"
        reports.append(IKReport(t, q, achieved, err, note))
    return reports


def main() -> None:
    rng = np.random.default_rng(0)
    reachable_r = L1 + L2

    # Mix of reachable, unreachable, and near-boundary targets.
    targets = np.array(
        [
            [0.50, 0.10],
            [0.30, 0.30],
            [0.10, 0.55],
            [0.65, 0.20],  # near boundary (max reach = 0.7)
            [0.70, 0.10],  # at boundary
            [0.80, 0.00],  # unreachable
            [-0.30, 0.40],
            [0.20, -0.40],
            [0.00, 0.00],  # at the base, the arm cannot collapse to a point
            [0.60, 0.40],  # outside reachable workspace
        ]
    )
    for _ in range(5):  # add 5 random reachable targets
        r = rng.uniform(0.1, 0.65)
        th = rng.uniform(0.0, math.pi)
        targets = np.vstack([targets, [r * math.cos(th), r * math.sin(th)]])

    reports = evaluate_targets(targets)
    success = sum(1 for r in reports if r.err is not None and r.err < 1e-6)
    print(f"max reach r_max = L1+L2 = {reachable_r:.3f}")
    print(f"targets evaluated: {len(reports)}, successes: {success}")
    print("-" * 78)
    print(f"{'idx':<3} {'target':<22} {'joints (deg)':<24} {'err':<10} {'note'}")
    for i, r in enumerate(reports):
        target_str = f"({r.target[0]:+.3f}, {r.target[1]:+.3f})"
        if r.joints is None:
            joint_str = "—"
            err_str = "—"
        else:
            j = np.degrees(r.joints)
            joint_str = f"({j[0]:+6.1f}, {j[1]:+6.1f})"
            err_str = f"{r.err:.2e}"
        print(f"{i:<3} {target_str:<22} {joint_str:<24} {err_str:<10} {r.note}")


if __name__ == "__main__":
    main()
