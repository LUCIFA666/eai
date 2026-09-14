"""4.1 — Synthetic chessboard camera calibration with OpenCV.

This script renders a virtual pinhole camera looking at a chessboard
target from many viewpoints, projects the world-frame board corners
onto the synthetic image plane, then runs ``cv2.calibrateCamera`` to
recover the intrinsics ``K`` and distortion coefficients.  Because we
control the ground truth, we can verify the recovered values to better
than 0.5% on a noiseless dataset (and report mm-level reprojection
error when small pixel noise is added).

Run:
    python labs/04-perception/camera_calibration_synthetic.py

Only ``numpy`` and ``opencv-python-headless`` are required.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

np.set_printoptions(precision=4, suppress=True, sign=" ")


# ---------------------------------------------------------------------------
# Ground-truth pinhole intrinsics and image size.
# ---------------------------------------------------------------------------
W, H = 1280, 720
FX_GT, FY_GT = 950.0, 950.0      # focal length in pixels
CX_GT, CY_GT = W / 2.0 + 4.0, H / 2.0 - 3.0  # principal point slightly off-centre

K_GT = np.array(
    [
        [FX_GT, 0.0, CX_GT],
        [0.0, FY_GT, CY_GT],
        [0.0, 0.0, 1.0],
    ]
)

# Use a small radial distortion to make the problem realistic.  Tangential is
# zero so we can validate that the solver leaves them ~0.
DIST_GT = np.array([-0.10, 0.04, 0.0, 0.0, 0.0])

# ---------------------------------------------------------------------------
# Chessboard target (inside corners).
# ---------------------------------------------------------------------------
COLS, ROWS = 9, 6                # interior corners
SQUARE = 0.025                   # 25 mm squares

object_points = np.zeros((COLS * ROWS, 3), dtype=np.float32)
object_points[:, :2] = np.mgrid[0:COLS, 0:ROWS].T.reshape(-1, 2) * SQUARE


def rodrigues_from_euler(rx: float, ry: float, rz: float) -> np.ndarray:
    """Return 3x3 rotation matrix from XYZ Euler angles (radians)."""
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def generate_views(seed: int = 0):
    """Return a deterministic list of (rvec, tvec) board-in-camera poses."""
    rng = np.random.default_rng(seed)
    poses = []
    # Sample views on a small arc so all corners stay inside the image.
    for tilt_deg in (-25, -15, -5, 5, 15, 25):
        for yaw_deg in (-20, 0, 20):
            for dist in (0.45, 0.55):
                R = rodrigues_from_euler(
                    math.radians(tilt_deg),
                    math.radians(yaw_deg),
                    math.radians(rng.uniform(-8, 8)),
                )
                # Centre the board roughly in front of the camera.
                t = np.array(
                    [
                        rng.uniform(-0.05, 0.05) - COLS * SQUARE * 0.5,
                        rng.uniform(-0.04, 0.04) - ROWS * SQUARE * 0.5,
                        dist,
                    ]
                )
                rvec, _ = cv2.Rodrigues(R)
                poses.append((rvec.flatten(), t))
    return poses


def project(rvec, tvec, noise_std: float, rng: np.random.Generator):
    proj, _ = cv2.projectPoints(object_points, rvec, tvec, K_GT, DIST_GT)
    proj = proj.reshape(-1, 2)
    if noise_std > 0:
        proj = proj + rng.normal(scale=noise_std, size=proj.shape)
    return proj.astype(np.float32)


def calibrate(noise_std: float, seed: int = 0):
    rng = np.random.default_rng(seed + 1)
    poses = generate_views(seed)
    image_points = []
    obj_points_list = []
    used = 0
    for rvec, tvec in poses:
        pts = project(rvec, tvec, noise_std, rng)
        if (
            pts[:, 0].min() < 4
            or pts[:, 0].max() > W - 4
            or pts[:, 1].min() < 4
            or pts[:, 1].max() > H - 4
        ):
            continue  # skip views where corners leave the sensor
        image_points.append(pts)
        obj_points_list.append(object_points)
        used += 1
    rms, K_est, dist_est, _, _ = cv2.calibrateCamera(
        obj_points_list, image_points, (W, H), None, None
    )
    return rms, K_est, dist_est.flatten(), used


def relative_error(true, est) -> float:
    return float(abs(est - true) / abs(true)) * 100.0


def main() -> None:
    print(f"image size = {W}x{H}, chessboard = {COLS}x{ROWS}, square = {SQUARE*1000:.0f} mm")
    print("ground-truth K =\n", K_GT)
    print("ground-truth dist =", DIST_GT)

    rows = []
    for noise in (0.0, 0.25, 0.5):
        rms, K, dist, used = calibrate(noise_std=noise)
        rows.append((noise, rms, K, dist, used))
        print(f"\n--- pixel noise std = {noise:.2f} px, views used = {used} ---")
        print("recovered K =\n", K)
        print("recovered dist =", dist)
        print(f"RMS reprojection error = {rms:.4f} px")
        print(
            "fx err = {:.3f}% | fy err = {:.3f}% | cx err = {:.3f}% | cy err = {:.3f}%".format(
                relative_error(FX_GT, K[0, 0]),
                relative_error(FY_GT, K[1, 1]),
                relative_error(CX_GT, K[0, 2]),
                relative_error(CY_GT, K[1, 2]),
            )
        )

    # ------------------------------------------------------------------
    # Pass / fail summary on the noiseless (ground-truth) calibration.
    # ------------------------------------------------------------------
    _, rms0, K0, dist0, used0 = rows[0]
    fx_err = relative_error(FX_GT, K0[0, 0])
    fy_err = relative_error(FY_GT, K0[1, 1])
    cx_err = relative_error(CX_GT, K0[0, 2])
    cy_err = relative_error(CY_GT, K0[1, 2])
    print(
        "\n>>> noiseless check: max relative intrinsic error = {:.4f}% (threshold 0.5%) | RMS = {:.2e} px | views = {}".format(
            max(fx_err, fy_err, cx_err, cy_err), rms0, used0
        )
    )
    assert max(fx_err, fy_err, cx_err, cy_err) < 0.5, "noiseless calibration drifted >0.5%"


if __name__ == "__main__":
    main()
