"""4.6 — 6-DoF object pose via Perspective-n-Point.

We treat a small cuboid (think: chemistry beaker base) as the target.
We know its 3D model points in the *object* frame.  The script:

1. Picks a ground-truth rigid pose ``T_cam_obj``.
2. Projects the model points to a synthetic camera (1024x768, fx=fy=900).
3. Adds Gaussian pixel noise.
4. Runs ``cv2.solvePnP`` with several solvers (ITERATIVE, EPNP, SQPNP)
   and reports rotation/translation error vs ground truth.
5. Also runs RANSAC PnP with 20% outlier correspondences and verifies
   it still recovers the pose.

Run:
    python labs/04-perception/pnp_pose.py
"""
from __future__ import annotations

import math
import os

import cv2
import numpy as np

np.set_printoptions(precision=4, suppress=True, sign=" ")


W, H = 1024, 768
FX = FY = 900.0
CX, CY = W / 2.0, H / 2.0
K = np.array([[FX, 0, CX], [0, FY, CY], [0, 0, 1]])
DIST = np.zeros(5)

RUN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs", "05-perception"))
os.makedirs(RUN_DIR, exist_ok=True)


def rot_xyz(rx, ry, rz):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def angle_axis_from_R(R):
    cos_theta = (np.trace(R) - 1.0) / 2.0
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return math.degrees(math.acos(cos_theta))


def make_object_points():
    """Return 14 model points on a 60 mm x 60 mm x 120 mm cuboid."""
    sx, sy, sz = 0.06, 0.06, 0.12
    base = np.array(
        [
            [-sx / 2, -sy / 2, 0],
            [sx / 2, -sy / 2, 0],
            [sx / 2, sy / 2, 0],
            [-sx / 2, sy / 2, 0],
            [-sx / 2, -sy / 2, sz],
            [sx / 2, -sy / 2, sz],
            [sx / 2, sy / 2, sz],
            [-sx / 2, sy / 2, sz],
            # Extra fiducial points on the side faces:
            [-sx / 2, 0, sz / 2],
            [sx / 2, 0, sz / 2],
            [0, -sy / 2, sz / 2],
            [0, sy / 2, sz / 2],
            [0, 0, 0],
            [0, 0, sz],
        ]
    )
    return base.astype(np.float64)


def pose_error(R_gt, t_gt, R_est, t_est):
    R_err = R_est.T @ R_gt
    rot_deg = angle_axis_from_R(R_err)
    t_err_mm = float(np.linalg.norm(t_est.flatten() - t_gt.flatten())) * 1000.0
    return rot_deg, t_err_mm


def project(R, t, obj_points, noise_std, rng):
    rvec, _ = cv2.Rodrigues(R)
    proj, _ = cv2.projectPoints(obj_points, rvec, t, K, DIST)
    proj = proj.reshape(-1, 2)
    if noise_std > 0:
        proj += rng.normal(scale=noise_std, size=proj.shape)
    return proj


def main():
    rng = np.random.default_rng(0)
    obj_points = make_object_points()

    # ---- Ground-truth object-in-camera pose ----
    R_gt = rot_xyz(math.radians(15), math.radians(-20), math.radians(35))
    t_gt = np.array([0.04, -0.03, 0.55])
    print("--- ground-truth pose ---")
    print("R =\n", R_gt)
    print("t =", t_gt, "(metres)")

    print(f"\nimage = {W}x{H}, focal = {FX} px, model points = {obj_points.shape[0]}")

    methods = [
        ("ITERATIVE", cv2.SOLVEPNP_ITERATIVE),
        ("EPNP", cv2.SOLVEPNP_EPNP),
        ("SQPNP", cv2.SOLVEPNP_SQPNP),
    ]

    print(f"\n{'method':10s} {'noise_px':>9s} {'rot_err_deg':>13s} {'t_err_mm':>10s} {'reproj_px':>10s}")
    rows = []
    for noise in (0.0, 0.5, 1.5):
        proj = project(R_gt, t_gt, obj_points, noise, rng)
        for name, flag in methods:
            ok, rvec, tvec = cv2.solvePnP(obj_points, proj.astype(np.float64), K, DIST, flags=flag)
            assert ok, f"{name} failed"
            R_est, _ = cv2.Rodrigues(rvec)
            rot_deg, t_mm = pose_error(R_gt, t_gt, R_est, tvec)
            re_proj, _ = cv2.projectPoints(obj_points, rvec, tvec, K, DIST)
            rep = float(np.mean(np.linalg.norm(re_proj.reshape(-1, 2) - proj, axis=1)))
            rows.append((name, noise, rot_deg, t_mm, rep))
            print(f"{name:10s} {noise:9.2f} {rot_deg:13.4f} {t_mm:10.4f} {rep:10.4f}")

    # ---- RANSAC PnP with 20% outliers ----
    proj = project(R_gt, t_gt, obj_points, noise_std=0.7, rng=rng)
    n_out = max(1, int(0.20 * proj.shape[0]))
    idx_out = rng.choice(proj.shape[0], size=n_out, replace=False)
    proj_bad = proj.copy()
    proj_bad[idx_out] += rng.normal(scale=50.0, size=(n_out, 2))  # large pixel errors
    print(f"\n--- RANSAC PnP with {n_out} outlier(s) out of {proj.shape[0]} ---")
    ok, rvec, tvec, inliers = cv2.solvePnPRansac(obj_points, proj_bad.astype(np.float64), K, DIST)
    R_est, _ = cv2.Rodrigues(rvec)
    rot_deg, t_mm = pose_error(R_gt, t_gt, R_est, tvec)
    n_inliers = 0 if inliers is None else inliers.shape[0]
    print(f"inliers = {n_inliers}/{proj_bad.shape[0]} | rot_err = {rot_deg:.4f} deg | t_err = {t_mm:.3f} mm")

    # Pass criteria.
    noiseless_rows = [r for r in rows if r[1] == 0.0]
    assert all(r[2] < 1e-3 for r in noiseless_rows), "noiseless PnP not exact"
    assert rot_deg < 2.0 and t_mm < 10.0, "RANSAC PnP failed with 20% outliers"

    with open(os.path.join(RUN_DIR, "pnp_pose.csv"), "w") as f:
        f.write("method,noise_px,rot_err_deg,t_err_mm,reproj_px\n")
        for r in rows:
            f.write(f"{r[0]},{r[1]:.2f},{r[2]:.4f},{r[3]:.4f},{r[4]:.4f}\n")
    print(f"\nwrote {os.path.join(RUN_DIR, 'pnp_pose.csv')}")
    print(">>> PASS: noiseless PnP exact, RANSAC PnP robust to 20% outliers.")


if __name__ == "__main__":
    main()
