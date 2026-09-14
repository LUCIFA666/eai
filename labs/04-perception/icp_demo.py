"""4.3 — ICP point-cloud registration.

We sample a synthetic "bunny-like" surface (two paraboloids + a flat
base), perturb a copy with a known rigid transform plus a small amount
of noise, then run Iterative Closest Point (ICP) to recover the
transform.  Two implementations are exercised:

1. A pure-numpy ICP that nearest-neighbour matches with a KD-tree from
   ``scipy.spatial`` if present, otherwise brute-force.  This is the
   reference implementation and always runs.
2. If ``open3d`` is installed, we additionally call
   ``open3d.pipelines.registration.registration_icp`` and report its
   answer for cross-validation.

Run:
    python labs/04-perception/icp_demo.py
"""
from __future__ import annotations

import math
import os

import numpy as np

np.set_printoptions(precision=4, suppress=True, sign=" ")


RUN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs", "05-perception"))
os.makedirs(RUN_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Synthetic source cloud.
# ---------------------------------------------------------------------------
def make_source(n: int = 3000, seed: int = 0) -> np.ndarray:
    """Two paraboloid bumps on a square base, deterministic."""
    rng = np.random.default_rng(seed)
    pts = []
    # Flat base.
    n_base = n // 3
    xy = rng.uniform(-0.5, 0.5, size=(n_base, 2))
    z = np.zeros(n_base)
    pts.append(np.column_stack([xy, z]))
    # Two bumps.
    for cx, cy in ((-0.15, 0.10), (0.18, -0.08)):
        n_bump = (n - n_base) // 2
        xy = rng.normal(loc=(cx, cy), scale=0.10, size=(n_bump, 2))
        r2 = (xy[:, 0] - cx) ** 2 + (xy[:, 1] - cy) ** 2
        z = 0.20 - 4.0 * r2
        z = np.clip(z, 0.0, 0.20)
        pts.append(np.column_stack([xy, z]))
    return np.concatenate(pts, axis=0)


def make_transform(roll_deg: float, pitch_deg: float, yaw_deg: float, t: np.ndarray) -> np.ndarray:
    r = math.radians(roll_deg)
    p = math.radians(pitch_deg)
    y = math.radians(yaw_deg)
    Rx = np.array([[1, 0, 0], [0, math.cos(r), -math.sin(r)], [0, math.sin(r), math.cos(r)]])
    Ry = np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])
    Rz = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
    R = Rz @ Ry @ Rx
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def apply_T(T: np.ndarray, pts: np.ndarray) -> np.ndarray:
    return (pts @ T[:3, :3].T) + T[:3, 3]


# ---------------------------------------------------------------------------
# Pure-numpy ICP (point-to-point, Umeyama closed form per iteration).
# ---------------------------------------------------------------------------
try:
    from scipy.spatial import cKDTree as _KDTree

    def _nn(query, ref):
        tree = _KDTree(ref)
        d, i = tree.query(query, k=1)
        return d, i

    _NN_BACKEND = "scipy.cKDTree"
except Exception:
    def _nn(query, ref):
        # Brute force.  Slow for large N but exact.
        diffs = query[:, None, :] - ref[None, :, :]
        dist = np.linalg.norm(diffs, axis=-1)
        i = np.argmin(dist, axis=1)
        d = dist[np.arange(query.shape[0]), i]
        return d, i

    _NN_BACKEND = "numpy brute force"


def umeyama(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Rigid (no scale) best fit.  ``src`` and ``dst`` are Nx3, paired."""
    mu_s = src.mean(axis=0)
    mu_d = dst.mean(axis=0)
    S = (src - mu_s).T @ (dst - mu_d) / src.shape[0]
    U, _, Vt = np.linalg.svd(S)
    D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[2, 2] = -1.0
    R = (U @ D @ Vt).T
    t = mu_d - R @ mu_s
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def icp(source: np.ndarray, target: np.ndarray, max_iter: int = 40, tol: float = 1e-7):
    """Classic point-to-point ICP starting from identity."""
    T_total = np.eye(4)
    src = source.copy()
    history = []
    prev_rmse = None
    for it in range(max_iter):
        d, i = _nn(src, target)
        rmse = float(np.sqrt(np.mean(d ** 2)))
        T_step = umeyama(src, target[i])
        src = apply_T(T_step, src)
        T_total = T_step @ T_total
        history.append((it, rmse))
        if prev_rmse is not None and abs(prev_rmse - rmse) < tol:
            break
        prev_rmse = rmse
    return T_total, history


def relative_error(true, est) -> float:
    diff = est @ np.linalg.inv(true)
    rot_err = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(diff[:3, :3]) - 1.0) / 2.0))))
    t_err = float(np.linalg.norm(diff[:3, 3]))
    return rot_err, t_err


def main() -> None:
    np.random.seed(0)
    source = make_source()
    T_gt = make_transform(roll_deg=4.0, pitch_deg=-6.0, yaw_deg=15.0, t=np.array([0.05, -0.03, 0.02]))
    target = apply_T(T_gt, source) + np.random.normal(scale=0.003, size=source.shape)

    print(f"NN backend: {_NN_BACKEND}")
    print(f"source: {source.shape}, target: {target.shape}")
    print("ground-truth T =\n", T_gt)

    T_est, history = icp(source, target)
    print("estimated T =\n", T_est)
    rot_err_deg, t_err = relative_error(T_gt, T_est)
    print(f"residual rotation error  = {rot_err_deg:.4f} deg")
    print(f"residual translation err = {t_err*1000:.3f} mm")
    print("ICP RMSE per iteration:")
    for it, rmse in history:
        print(f"  iter {it:02d}  rmse = {rmse*1000:.3f} mm")

    np.savetxt(
        os.path.join(RUN_DIR, "icp_history.csv"),
        np.array(history),
        delimiter=",",
        header="iter,rmse_m",
        comments="",
    )

    # --- Optional Open3D cross-check ---
    try:
        import open3d as o3d

        src_pcd = o3d.geometry.PointCloud()
        src_pcd.points = o3d.utility.Vector3dVector(source)
        tgt_pcd = o3d.geometry.PointCloud()
        tgt_pcd.points = o3d.utility.Vector3dVector(target)
        reg = o3d.pipelines.registration.registration_icp(
            src_pcd,
            tgt_pcd,
            max_correspondence_distance=0.05,
            estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPoint(),
            criteria=o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=40),
        )
        print("open3d ICP fitness =", reg.fitness)
        print("open3d ICP RMSE    =", reg.inlier_rmse)
        rot_err_o3d, t_err_o3d = relative_error(T_gt, np.asarray(reg.transformation))
        print(f"open3d residual rot err = {rot_err_o3d:.4f} deg, trans err = {t_err_o3d*1000:.3f} mm")
    except Exception as exc:
        print(f"open3d unavailable, skipped cross-check ({exc.__class__.__name__})")

    assert rot_err_deg < 1.0, "ICP rotation error >1 deg"
    assert t_err < 0.01, "ICP translation error >10 mm"
    print(">>> PASS: ICP recovered transform within 1 deg, 10 mm.")


if __name__ == "__main__":
    main()
