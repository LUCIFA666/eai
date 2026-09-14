"""3.1 — SE(3) rigid-body transforms in plain numpy.

This script reproduces the ``T_world_base @ T_base_ee @ p_ee`` chain
covered in section 03 of the curriculum.  No external dependencies
beyond numpy so it works on any Python 3.9+ install.

Run:
    python labs/03-robotics/se3_transforms.py

It prints a deterministic table that should match
``runs/03-robotics/se3_transforms.txt``.
"""
from __future__ import annotations

import math

import numpy as np

np.set_printoptions(precision=4, suppress=True, sign=" ")


def rot_x(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def make_T(R: np.ndarray, p: np.ndarray) -> np.ndarray:
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = p
    return T


def invert_T(T: np.ndarray) -> np.ndarray:
    """Inverse of an SE(3) matrix using R^T and -R^T p, not np.linalg.inv."""
    R = T[:3, :3]
    p = T[:3, 3]
    T_inv = np.eye(4)
    T_inv[:3, :3] = R.T
    T_inv[:3, 3] = -R.T @ p
    return T_inv


def quat_from_R(R: np.ndarray) -> np.ndarray:
    """Return unit quaternion ``[w, x, y, z]`` from rotation matrix.

    Uses Shepperd's method which is numerically stable for any input
    rotation.  Sign is fixed so ``w >= 0``.
    """
    trace = R[0, 0] + R[1, 1] + R[2, 2]
    if trace > 0:
        s = 0.5 / math.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2, 1] - R[1, 2]) * s
        y = (R[0, 2] - R[2, 0]) * s
        z = (R[1, 0] - R[0, 1]) * s
    else:
        i = int(np.argmax([R[0, 0], R[1, 1], R[2, 2]]))
        if i == 0:
            s = 2.0 * math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif i == 1:
            s = 2.0 * math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
    q = np.array([w, x, y, z])
    if q[0] < 0:
        q = -q
    return q / np.linalg.norm(q)


def main() -> None:
    # Define a base frame at (1, 0, 0) and rotated 30° about z.
    T_world_base = make_T(rot_z(math.radians(30)), np.array([1.0, 0.0, 0.0]))

    # End-effector relative to base: 45° pitch + offset along x.
    T_base_ee = make_T(rot_y(math.radians(45)), np.array([0.3, 0.0, 0.4]))

    T_world_ee = T_world_base @ T_base_ee

    # Express a point in the ee frame and transform it.
    p_ee = np.array([0.0, 0.0, 0.1, 1.0])  # 10 cm above the ee origin.
    p_world = T_world_ee @ p_ee

    # Round-trip check: invert the composed transform and recover p_ee.
    p_ee_recovered = invert_T(T_world_ee) @ p_world
    err = np.linalg.norm(p_ee_recovered - p_ee)

    print("T_world_base =\n", T_world_base)
    print("T_base_ee   =\n", T_base_ee)
    print("T_world_ee  =\n", T_world_ee)
    print("p_ee        =", p_ee)
    print("p_world     =", p_world)
    print("p_ee round-trip =", p_ee_recovered)
    print(f"round-trip error = {err:.3e}")
    q = quat_from_R(T_world_ee[:3, :3])
    print("quaternion (w,x,y,z) =", q)
    print(f"||q|| = {np.linalg.norm(q):.6f}")

    # Failure mode demo: wrong composition order.
    wrong = T_base_ee @ T_world_base  # do NOT write transforms this way.
    diff = np.linalg.norm(wrong - T_world_ee)
    print(f"swap order error (should be > 0): {diff:.4f}")


if __name__ == "__main__":
    main()
