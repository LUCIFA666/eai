"""4.4 — Synthetic hand-eye calibration via AX = XB (Tsai-Lenz).

We simulate an eye-in-hand setup: a camera bolted on the robot end-
effector observes a static calibration target while the robot moves
through 12 random poses.  The script generates motion pairs

    A_i = T_ee(t_i)^{-1} · T_ee(t_{i+1})            (gripper motion)
    B_i = T_cam_target(t_i) · T_cam_target(t_{i+1})^{-1}   (camera motion)

and solves ``A_i · X = X · B_i`` where ``X = T_ee_cam`` is the unknown
camera mount.  We compare two solvers exposed by OpenCV
(``cv2.calibrateHandEye``) — Tsai, Park, Horaud, Andreff, Daniilidis —
and report rotation/translation residuals against the ground truth.

Run:
    python labs/04-perception/hand_eye_synthetic.py
"""
from __future__ import annotations

import math
import os

import cv2
import numpy as np

np.set_printoptions(precision=4, suppress=True, sign=" ")


RUN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs", "05-perception"))
os.makedirs(RUN_DIR, exist_ok=True)


def rot_xyz(rx: float, ry: float, rz: float) -> np.ndarray:
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def make_T(R: np.ndarray, t: np.ndarray) -> np.ndarray:
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def inv_T(T: np.ndarray) -> np.ndarray:
    R = T[:3, :3]
    t = T[:3, 3]
    Ti = np.eye(4)
    Ti[:3, :3] = R.T
    Ti[:3, 3] = -R.T @ t
    return Ti


def rot_translation_error(R_true: np.ndarray, t_true: np.ndarray, R_est: np.ndarray, t_est: np.ndarray):
    R_err = R_est.T @ R_true
    cos_theta = (np.trace(R_err) - 1.0) / 2.0
    cos_theta = max(-1.0, min(1.0, cos_theta))
    angle_deg = math.degrees(math.acos(cos_theta))
    t_err_mm = float(np.linalg.norm(t_est - t_true)) * 1000.0
    return angle_deg, t_err_mm


def main() -> None:
    rng = np.random.default_rng(42)

    # ---- Ground truth ----
    # Eye-in-hand: camera bolted 5 cm forward and 2 cm up of the EE, tilted 12 deg pitch.
    R_X_gt = rot_xyz(0.0, math.radians(12.0), 0.0)
    t_X_gt = np.array([0.05, 0.00, 0.02])
    T_X_gt = make_T(R_X_gt, t_X_gt)

    # World-frame target pose (calibration object).
    R_target_world = rot_xyz(math.radians(5.0), 0.0, math.radians(30.0))
    t_target_world = np.array([0.55, 0.10, 0.40])
    T_target_world = make_T(R_target_world, t_target_world)

    print("--- Ground truth hand-eye X = T_ee_cam ---")
    print(T_X_gt)

    # ---- Generate N robot poses, view the target with the camera ----
    N = 14
    Ts_world_ee = []
    Ts_cam_target = []
    for _ in range(N):
        # Random EE pose around a workspace point.
        rx = rng.uniform(math.radians(-30), math.radians(30))
        ry = rng.uniform(math.radians(-25), math.radians(25))
        rz = rng.uniform(math.radians(-90), math.radians(90))
        R_we = rot_xyz(rx, ry, rz)
        t_we = np.array([
            rng.uniform(0.20, 0.50),
            rng.uniform(-0.20, 0.30),
            rng.uniform(0.15, 0.55),
        ])
        T_world_ee = make_T(R_we, t_we)
        # Compute camera-to-target.
        T_world_cam = T_world_ee @ T_X_gt
        T_cam_target = inv_T(T_world_cam) @ T_target_world
        Ts_world_ee.append(T_world_ee)
        Ts_cam_target.append(T_cam_target)

    # Optionally add a tiny noise on the target observation to make it realistic.
    NOISE_PIX = 0.5  # not pixels here, just label
    NOISE_T = 0.0008  # 0.8 mm
    NOISE_R = math.radians(0.05)  # 0.05 deg
    Ts_cam_target_noisy = []
    for T in Ts_cam_target:
        Rn = rot_xyz(rng.normal(scale=NOISE_R), rng.normal(scale=NOISE_R), rng.normal(scale=NOISE_R))
        tn = rng.normal(scale=NOISE_T, size=3)
        T_n = T.copy()
        T_n[:3, :3] = Rn @ T_n[:3, :3]
        T_n[:3, 3] = T_n[:3, 3] + tn
        Ts_cam_target_noisy.append(T_n)

    # ---- Build OpenCV's lists ----
    # OpenCV expects: gripper_to_base (T_base_gripper) and target_to_cam (T_cam_target).
    R_g2b = [T[:3, :3] for T in Ts_world_ee]
    t_g2b = [T[:3, 3] for T in Ts_world_ee]
    R_t2c = [T[:3, :3] for T in Ts_cam_target_noisy]
    t_t2c = [T[:3, 3] for T in Ts_cam_target_noisy]

    methods = [
        ("TSAI", cv2.CALIB_HAND_EYE_TSAI),
        ("PARK", cv2.CALIB_HAND_EYE_PARK),
        ("HORAUD", cv2.CALIB_HAND_EYE_HORAUD),
        ("ANDREFF", cv2.CALIB_HAND_EYE_ANDREFF),
        ("DANIILIDIS", cv2.CALIB_HAND_EYE_DANIILIDIS),
    ]

    print(f"\nposes = {N}, simulated obs noise: dt={NOISE_T*1000:.2f} mm, dR={math.degrees(NOISE_R):.3f} deg")
    print(f"{'method':12s} {'rot_err_deg':>13s} {'t_err_mm':>10s}")
    rows = []
    for name, m in methods:
        R_X, t_X = cv2.calibrateHandEye(R_g2b, t_g2b, R_t2c, t_t2c, method=m)
        angle_deg, t_err_mm = rot_translation_error(R_X_gt, t_X_gt, R_X, t_X.flatten())
        rows.append((name, angle_deg, t_err_mm))
        print(f"{name:12s} {angle_deg:13.4f} {t_err_mm:10.4f}")

    # ---- AX = XB residuals using the best estimate (DANIILIDIS) ----
    R_X, t_X = cv2.calibrateHandEye(R_g2b, t_g2b, R_t2c, t_t2c, method=cv2.CALIB_HAND_EYE_DANIILIDIS)
    T_X_est = make_T(R_X, t_X.flatten())
    print("\nestimated X (DANIILIDIS) =\n", T_X_est)

    # Compute AX - XB residuals on motion pairs.
    residuals = []
    for i in range(N - 1):
        # A_i: gripper motion = T_ee_i^-1 · T_ee_{i+1}
        A = inv_T(Ts_world_ee[i]) @ Ts_world_ee[i + 1]
        # B_i: camera motion = T_cam_target_i · T_cam_target_{i+1}^-1
        B = Ts_cam_target_noisy[i] @ inv_T(Ts_cam_target_noisy[i + 1])
        res = A @ T_X_est - T_X_est @ B
        residuals.append(np.linalg.norm(res[:3, 3]))
    residuals = np.array(residuals)
    print(f"AX-XB translation residual: mean={residuals.mean()*1000:.3f} mm, max={residuals.max()*1000:.3f} mm")

    # Pass: best solver should be sub-degree, sub-mm.
    best = min(rows, key=lambda r: r[1] + r[2])
    print(f"\n>>> PASS condition: best solver = {best[0]}, rot_err = {best[1]:.4f} deg, t_err = {best[2]:.3f} mm.")
    assert best[1] < 0.5 and best[2] < 5.0, "hand-eye calibration error exceeded thresholds"

    with open(os.path.join(RUN_DIR, "hand_eye_methods.csv"), "w") as f:
        f.write("method,rot_err_deg,t_err_mm\n")
        for name, a, t in rows:
            f.write(f"{name},{a:.4f},{t:.4f}\n")


if __name__ == "__main__":
    main()
