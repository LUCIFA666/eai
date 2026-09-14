"""3.3-3.5 — Self-contained MuJoCo FK/Jacobian/DLS-IK demo on a 3-link arm.

Many learners hit network issues fetching ``mujoco_menagerie``. This
script builds a 3-link planar-ish arm directly from an inline MJCF
string so it runs anywhere ``mujoco>=3.0`` is installed.  It exercises
the same APIs (``mj_kinematics``, ``mj_jacBody``, DLS update) that you
will use on the Franka Panda later.

Run:
    python labs/03-robotics/mujoco_inline_panda_like.py

Outputs:
- prints FK table + DLS IK convergence trace
- writes ``runs/03-robotics/mujoco_inline_arm.txt``
- writes ``runs/03-robotics/mujoco_inline_arm_ik.csv``
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

try:
    import mujoco
except ImportError as exc:
    raise SystemExit("install mujoco>=3.0") from exc

# A 3-link revolute arm with link lengths 0.30, 0.25, 0.20 (m).
# Axes alternate so the workspace is 3D and Jacobian is full rank.
MJCF = """
<mujoco model="threelink">
  <option gravity="0 0 -9.81"/>
  <worldbody>
    <body name="link1" pos="0 0 0">
      <joint name="j1" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
      <geom type="capsule" fromto="0 0 0 0.30 0 0" size="0.04" rgba="0.6 0.6 0.7 1"/>
      <body name="link2" pos="0.30 0 0">
        <joint name="j2" type="hinge" axis="0 1 0" range="-2.5 2.5"/>
        <geom type="capsule" fromto="0 0 0 0.25 0 0" size="0.035" rgba="0.6 0.7 0.6 1"/>
        <body name="link3" pos="0.25 0 0">
          <joint name="j3" type="hinge" axis="0 1 0" range="-2.5 2.5"/>
          <geom type="capsule" fromto="0 0 0 0.20 0 0" size="0.03" rgba="0.7 0.6 0.6 1"/>
          <body name="ee" pos="0.20 0 0">
            <geom type="sphere" size="0.02" rgba="0.9 0.3 0.3 1"/>
          </body>
        </body>
      </body>
    </body>
  </worldbody>
  <actuator>
    <position joint="j1" kp="50"/>
    <position joint="j2" kp="50"/>
    <position joint="j3" kp="50"/>
  </actuator>
</mujoco>
"""

REPO_ROOT = Path(__file__).resolve().parents[2]


def fk_table(model: "mujoco.MjModel", data: "mujoco.MjData", ee_bid: int) -> list[str]:
    """Print FK for 5 canonical poses, returning text lines."""
    poses = [
        ("home",             np.array([0.0, 0.0, 0.0])),
        ("elbow_45",         np.array([0.0, 0.78, 0.0])),
        ("shoulder_30",      np.array([0.52, 0.40, 0.30])),
        ("reach_forward",    np.array([0.0, 0.20, 0.20])),
        ("near_singular",    np.array([0.0, 0.0, 0.01])),  # arm nearly straight
    ]
    lines = [f"{'config':<16} {'x':>7} {'y':>7} {'z':>7} {'qw':>7} {'qx':>7} {'qy':>7} {'qz':>7}"]
    for name, q in poses:
        data.qpos[:] = q
        mujoco.mj_kinematics(model, data)
        pos = data.xpos[ee_bid]
        quat = data.xquat[ee_bid]
        lines.append(
            f"{name:<16} {pos[0]:>+7.3f} {pos[1]:>+7.3f} {pos[2]:>+7.3f}"
            f" {quat[0]:>+7.3f} {quat[1]:>+7.3f} {quat[2]:>+7.3f} {quat[3]:>+7.3f}"
        )
    return lines


def dls_ik(model: "mujoco.MjModel", data: "mujoco.MjData", ee_bid: int,
           target: np.ndarray, *, max_iter: int = 80, dls_lambda: float = 0.05,
           step_scale: float = 0.5, tol: float = 1e-4):
    jac_p = np.zeros((3, model.nv))
    jac_r = np.zeros((3, model.nv))
    trace = []
    for it in range(max_iter):
        mujoco.mj_forward(model, data)
        err = target - data.xpos[ee_bid]
        err_norm = float(np.linalg.norm(err))
        mujoco.mj_jacBody(model, data, jac_p, jac_r, ee_bid)
        J = jac_p[:, :model.nv]
        s = np.linalg.svd(J, compute_uv=False)
        smin = float(s.min())
        smax = float(s.max())
        trace.append((it, err_norm, smin, smax))
        if err_norm < tol:
            break
        damped = J @ J.T + (dls_lambda ** 2) * np.eye(3)
        dq = J.T @ np.linalg.solve(damped, err)
        data.qpos[:model.nv] += step_scale * dq
    return trace


def main() -> None:
    model = mujoco.MjModel.from_xml_string(MJCF)
    data = mujoco.MjData(model)
    ee_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ee")
    if ee_bid == -1:
        raise SystemExit("ee body not found")

    out_dir = REPO_ROOT / "runs/03-robotics"
    out_dir.mkdir(parents=True, exist_ok=True)

    # FK table
    lines = fk_table(model, data, ee_bid)
    txt = "\n".join(lines)
    print(txt)
    (out_dir / "mujoco_inline_arm.txt").write_text(txt + "\n", encoding="utf-8")

    # DLS IK from ready pose to a 5 cm offset
    data.qpos[:] = [0.0, 0.78, 0.0]
    mujoco.mj_forward(model, data)
    start = data.xpos[ee_bid].copy()
    target = start + np.array([0.05, 0.03, 0.04])
    print(f"\nstart_ee={start}, target={target}")
    trace = dls_ik(model, data, ee_bid, target)
    print(f"iter   err_norm    smin       smax       cond")
    for it, err, smin, smax in trace:
        cond = smax / smin if smin > 1e-12 else float("inf")
        if it % 5 == 0 or it == len(trace) - 1:
            print(f"{it:5d}  {err:.4e}  {smin:.3e}  {smax:.3e}  {cond:.2e}")
    print(f"converged in {len(trace)} iters, final err={trace[-1][1]:.3e}")
    print(f"final qpos = {data.qpos[:]}")

    csv_path = out_dir / "mujoco_inline_arm_ik.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iter", "err_norm", "smin", "smax", "cond"])
        for it, err, smin, smax in trace:
            cond = smax / smin if smin > 1e-12 else float("inf")
            w.writerow([it, err, smin, smax, cond])
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
