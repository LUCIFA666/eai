"""3.5-3.6 — Jacobian, singularities, and differential IK with MuJoCo.

Computes the analytic body Jacobian via ``mj_jacBody``, runs a
damped-least-squares (DLS) differential IK to a 5-cm offset target,
and reports the singular values along the way (so we can see the
condition number explode near singularities).

Run:
    python labs/03-robotics/mujoco_jacobian.py

Outputs:
- table of iteration → ee error → min/max singular value
- ``runs/03-robotics/panda_dls_ik.csv``
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

try:
    import mujoco
except ImportError as exc:
    raise SystemExit("install mujoco>=3.0") from exc

REPO_ROOT = Path(__file__).resolve().parents[2]
PANDA_XML = REPO_ROOT / "reference/mujoco_menagerie/franka_emika_panda/panda.xml"
PANDA_URDF_FALLBACK = Path(
    "/data/rbc/curobo/src/curobo/content/assets/robot/franka_description/panda.urdf"
)


def find_ee_body(model: "mujoco.MjModel") -> int:
    for name in [
        "attachment", "hand", "panda_hand", "right_hand", "ee_link",
        "panda_link8", "panda_link7",
    ]:
        bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
        if bid != -1:
            return bid
    return model.nbody - 1


def resolve_panda_model() -> Path:
    if PANDA_XML.exists():
        return PANDA_XML
    if PANDA_URDF_FALLBACK.exists():
        return PANDA_URDF_FALLBACK
    raise SystemExit(
        f"Panda model not found. Clone mujoco_menagerie or install curobo."
    )


def run_dls_ik(
    model: "mujoco.MjModel",
    data: "mujoco.MjData",
    ee_bid: int,
    target_pos: np.ndarray,
    *,
    max_iter: int = 80,
    dls_lambda: float = 0.05,
    step_scale: float = 0.5,
    tol: float = 1e-4,
) -> list[tuple[int, float, float, float]]:
    """Damped-least-squares position-only IK. Returns iteration trace."""
    jac_p = np.zeros((3, model.nv))
    jac_r = np.zeros((3, model.nv))
    trace: list[tuple[int, float, float, float]] = []
    for it in range(max_iter):
        mujoco.mj_forward(model, data)
        ee_pos = data.xpos[ee_bid].copy()
        err = target_pos - ee_pos
        err_norm = float(np.linalg.norm(err))
        # 3xN positional Jacobian
        mujoco.mj_jacBody(model, data, jac_p, jac_r, ee_bid)
        # restrict to first 7 arm joints (skip fingers)
        n_arm = min(7, model.nv)
        J = jac_p[:, :n_arm]
        s = np.linalg.svd(J, compute_uv=False)
        smin, smax = float(s.min()), float(s.max())
        trace.append((it, err_norm, smin, smax))
        if err_norm < tol:
            break
        # Damped least squares: dq = J^T (J J^T + lam^2 I)^{-1} err
        JJt = J @ J.T
        damped = JJt + (dls_lambda ** 2) * np.eye(3)
        dq = J.T @ np.linalg.solve(damped, err)
        # update arm joints only; clip step
        data.qpos[:n_arm] += step_scale * dq
    return trace


def main() -> None:
    model_path = resolve_panda_model()
    print(f"loaded {model_path}")
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    ee_bid = find_ee_body(model)
    print(f"using ee body id={ee_bid} name={mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, ee_bid)!r}")

    # ready pose
    ready = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785])
    n_arm = min(7, model.nv)
    data.qpos[:n_arm] = ready[:n_arm]
    mujoco.mj_forward(model, data)
    start_pos = data.xpos[ee_bid].copy()
    target = start_pos + np.array([0.05, 0.05, 0.05])
    print(f"start pos = {start_pos}, target = {target}")

    trace = run_dls_ik(model, data, ee_bid, target)
    out = REPO_ROOT / "runs/03-robotics/panda_dls_ik.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iter", "err_norm", "smin", "smax", "cond"])
        for it, err, smin, smax in trace:
            cond = smax / smin if smin > 1e-12 else float("inf")
            w.writerow([it, err, smin, smax, cond])
            if it % 10 == 0 or it == len(trace) - 1:
                print(f"  iter={it:3d} err={err:.4e} smin={smin:.3e} smax={smax:.3e} cond={cond:.2e}")
    print(f"converged in {len(trace)} iters, final err={trace[-1][1]:.3e}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
