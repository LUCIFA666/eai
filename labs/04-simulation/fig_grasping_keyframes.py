"""4.6 — Figure: grasping 4-phase keyframe poses.

Produces the clean, labelled 4-phase composite (reach / grasp / lift / place)
for the grasping walkthrough. This is a lightweight FIGURE generator: it skips
dynamics, solves kinematic IK to place the hand at each phase target, teleports
the block to a plausible held/placed position, and renders. For the real
dynamic result, see grasping_pipeline.py.

Menagerie location: $MUJOCO_MENAGERIE if set, else reference/mujoco_menagerie.

Run:
    MUJOCO_GL=egl python labs/04-simulation/fig_grasping_keyframes.py

Outputs:
    runs/04-simulation/fig_grasping_phase_{1..4}.png
    runs/04-simulation/fig_grasping_keyframes.png   (2x2 composite)
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

os.environ.setdefault("MUJOCO_GL", "egl")

try:
    import mujoco
except ImportError as exc:
    raise RuntimeError("mujoco missing") from exc

try:
    import imageio.v3 as iio
except ImportError as exc:
    raise RuntimeError("imageio[ffmpeg] missing") from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

MENAGERIE = Path(os.environ.get("MUJOCO_MENAGERIE", ROOT / "reference" / "mujoco_menagerie"))
PANDA_DIR = MENAGERIE / "franka_emika_panda"
TMP_SCENE = PANDA_DIR / "_grasping_keyframes_tmp.xml"

GRASPING_XML = """<mujoco model="grasping_scene">
  <include file="scene.xml"/>
  <worldbody>
    <body name="table" pos="0.4 0 0.395">
      <geom name="table_top" type="box" size="0.3 0.4 0.02"
            rgba="0.6 0.4 0.2 1" friction="0.8 0.01 0.001"/>
    </body>
    <body name="block" pos="0.4 0 0.48">
      <joint type="free"/>
      <geom name="block_geom" type="box" size="0.03 0.03 0.03"
            mass="0.05" rgba="0.2 0.6 1 1" friction="1.0 0.01 0.001"/>
    </body>
    <site name="target_site" pos="0.4 0.2 0.44"
          type="sphere" size="0.01" rgba="0 1 0 0.5"/>
    <camera name="capture" pos="1.2 -0.6 0.9" xyaxes="0.6 0.8 0 -0.3 0.2 0.9" fovy="45"/>
  </worldbody>
</mujoco>
"""

HOME_ARM = np.array([0.0, 0.0, 0.0, -np.pi / 2, 0.0, np.pi / 2, -np.pi / 4])

PHASES = {
    "phase_1_reach": dict(target=np.array([0.40, 0.00, 0.62]), fingers=[0.04, 0.04],
                          block=[0.40, 0.00, 0.445]),
    "phase_2_grasp": dict(target=np.array([0.40, 0.00, 0.55]), fingers=[0.018, 0.018],
                          block=[0.40, 0.00, 0.445]),
    "phase_3_lift": dict(target=np.array([0.40, 0.00, 0.70]), fingers=[0.018, 0.018],
                         block=[0.40, 0.00, 0.595]),
    "phase_4_place": dict(target=np.array([0.40, 0.20, 0.55]), fingers=[0.04, 0.04],
                          block=[0.40, 0.20, 0.445]),
}


def solve_ik(model, data, target_pos, *, max_iter: int = 400, tol: float = 1e-3) -> float:
    """Damped least-squares IK on the hand body origin (kinematic).

    mj_jac's point is in WORLD coords, so we pass the hand origin's world
    position data.body("hand").xpos (passing np.zeros(3) would be a lever-arm
    bug that makes IK converge slowly/wrongly).
    """
    hand_id = data.body("hand").id
    jacp = np.zeros((3, model.nv))
    damping = 0.05
    eye3 = np.eye(3)
    err_norm = float("inf")
    for _ in range(max_iter):
        mujoco.mj_forward(model, data)
        err = target_pos - data.body("hand").xpos
        err_norm = float(np.linalg.norm(err))
        if err_norm < tol:
            return err_norm
        mujoco.mj_jac(model, data, jacp, None, data.body("hand").xpos, hand_id)
        J = jacp[:, :7]
        dq = J.T @ np.linalg.solve(J @ J.T + damping * eye3, err)
        data.qpos[:7] += dq * 0.5
        for j in range(7):
            lo, hi = model.jnt_range[j]
            data.qpos[j] = float(np.clip(data.qpos[j], lo, hi))
    return err_norm


def set_phase(model, data, phase: dict) -> float:
    data.qpos[:7] = HOME_ARM
    if model.nq >= 9:
        data.qpos[7:9] = phase["fingers"]
    err = solve_ik(model, data, phase["target"])
    if model.nq >= 9:
        data.qpos[7:9] = phase["fingers"]
    bjoint = model.body_jntadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "block")]
    adr = model.jnt_qposadr[bjoint]
    data.qpos[adr:adr + 3] = phase["block"]
    data.qpos[adr + 3:adr + 7] = [1, 0, 0, 0]
    mujoco.mj_forward(model, data)
    return err


def render_phase(model, data, name: str) -> np.ndarray:
    with mujoco.Renderer(model, height=360, width=480) as r:
        r.update_scene(data, camera="capture")
        img = r.render().copy()
    out = RUNS / f"fig_grasping_{name}.png"
    iio.imwrite(str(out), img)
    print(f"[write] {out}")
    return img


def main() -> None:
    if not PANDA_DIR.exists():
        raise SystemExit(f"Panda dir not found at {PANDA_DIR} "
                         f"(set MUJOCO_MENAGERIE or clone into reference/)")
    TMP_SCENE.write_text(GRASPING_XML)
    try:
        model = mujoco.MjModel.from_xml_path(str(TMP_SCENE))
        data = mujoco.MjData(model)
        frames: list[np.ndarray] = []
        for name, phase in PHASES.items():
            err = set_phase(model, data, phase)
            print(f"[{name}] target={phase['target'].tolist()}  "
                  f"hand_at={np.round(data.body('hand').xpos, 3).tolist()}  err={err:.4f}")
            frames.append(render_phase(model, data, name))
        top = np.concatenate([frames[0], frames[1]], axis=1)
        bot = np.concatenate([frames[2], frames[3]], axis=1)
        grid = np.concatenate([top, bot], axis=0)
        iio.imwrite(str(RUNS / "fig_grasping_keyframes.png"), grid)
        print(f"[write] {RUNS / 'fig_grasping_keyframes.png'}  shape={grid.shape}")
    finally:
        if TMP_SCENE.exists():
            TMP_SCENE.unlink()


if __name__ == "__main__":
    main()
