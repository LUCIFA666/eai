"""4.6 — Full pick-and-place pipeline (backs the grasping walkthrough).

Reproduces section/.../06-grasping-walkthrough/04-full-pick-pipeline.md:
  - damped-least-squares (DLS) IK solved KINEMATICALLY on a scratch MjData
    (so it never diverges), then position-actuator execution via mj_step.
  - state machine: REACH -> DESCEND -> GRASP -> LIFT -> MOVE -> PLACE.

Pass criteria: the block is lifted clear of the table, then ends within ~3 cm
(xy) of target_site, back on the table.

Note on mj_jac: its `point` argument is in WORLD coordinates, so passing
data.body("hand").xpos (the hand origin in world coords) is correct. Passing
np.zeros(3) would ask for a different point and make IK converge slowly/wrongly.

Menagerie location: $MUJOCO_MENAGERIE if set, else reference/mujoco_menagerie.

Run:
    MUJOCO_GL=egl python labs/04-simulation/grasping_pipeline.py

Outputs:
    runs/04-simulation/grasping_pipeline.txt
    runs/04-simulation/grasping_pipeline_video.mp4
    runs/04-simulation/grasping_pipeline_keyframes.png
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
except ImportError:
    iio = None

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

MENAGERIE = Path(os.environ.get("MUJOCO_MENAGERIE", ROOT / "reference" / "mujoco_menagerie"))
# Write the scene XML INSIDE the menagerie panda dir so the <include> and
# panda.xml's <compiler meshdir="assets"/> both resolve (paths are relative to
# the top-level XML's directory).
MENAGERIE_PANDA = (MENAGERIE / "franka_emika_panda").resolve()
TMP_SCENE = MENAGERIE_PANDA / "_grasping_scene_tmp.xml"

GRASPING_XML = """<mujoco model="grasping_scene">
  <include file="scene.xml"/>
  <worldbody>
    <light name="top_light" pos="0.4 0 2" dir="0 0 -1" directional="true"
           diffuse="0.8 0.8 0.8" specular="0.2 0.2 0.2"/>
    <body name="table" pos="0.4 0 0.395">
      <geom name="table_top" type="box" size="0.3 0.4 0.02"
            rgba="0.6 0.4 0.2 1" friction="0.8 0.01 0.001"/>
    </body>
    <body name="block" pos="0.4 0 0.48">
      <joint type="free"/>
      <geom name="block_geom" type="box" size="0.03 0.03 0.03"
            mass="0.05" rgba="0.2 0.6 1 1" friction="1.0 0.01 0.001"/>
    </body>
    <site name="target_site" pos="0.4 0.2 0.44" type="sphere" size="0.01" rgba="0 1 0 0.5"/>
    <camera name="capture" pos="1.3 -0.9 0.9" xyaxes="0.6 0.8 0 -0.35 0.26 0.9" fovy="42"/>
  </worldbody>
</mujoco>
"""

READY = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785])
GRASP_OFFSET = 0.103
OPEN, CLOSE = 255, 0


def main() -> None:
    if not MENAGERIE_PANDA.exists():
        raise SystemExit(f"menagerie panda not found at {MENAGERIE_PANDA} "
                         f"(set MUJOCO_MENAGERIE or clone into reference/)")

    TMP_SCENE.write_text(GRASPING_XML)
    try:
        model = mujoco.MjModel.from_xml_path(str(TMP_SCENE))
    finally:
        TMP_SCENE.unlink()

    data = mujoco.MjData(model)
    ik_data = mujoco.MjData(model)
    hand = data.body("hand").id
    arm_limit = model.jnt_range[:7].copy()

    renderer = mujoco.Renderer(model, height=360, width=480) if iio else None
    frames: list[np.ndarray] = []
    keyframes: dict[str, np.ndarray] = {}

    def snap():
        if renderer is not None:
            renderer.update_scene(data, camera="capture")
            frames.append(renderer.render().copy())

    def solve_ik(q_init, target, iters=300, damping=0.1, gain=0.5, clip=0.1):
        ik_data.qpos[:] = data.qpos
        ik_data.qpos[:7] = q_init
        mujoco.mj_forward(model, ik_data)
        jacp = np.zeros((3, model.nv))
        eye = np.eye(3)
        for _ in range(iters):
            err = target - ik_data.body("hand").xpos
            if np.linalg.norm(err) < 1e-3:
                break
            mujoco.mj_jac(model, ik_data, jacp, None, ik_data.body("hand").xpos, hand)
            J = jacp[:, :7]
            dq = J.T @ np.linalg.solve(J @ J.T + damping * eye, err * gain)
            ik_data.qpos[:7] = np.clip(ik_data.qpos[:7] + np.clip(dq, -clip, clip),
                                       arm_limit[:, 0], arm_limit[:, 1])
            mujoco.mj_forward(model, ik_data)
        return ik_data.qpos[:7].copy()

    def drive(arm_target, gripper, steps, rec=4):
        for i in range(steps):
            data.ctrl[:7] = arm_target
            data.ctrl[7] = gripper
            mujoco.mj_step(model, data)
            if i % rec == 0:
                snap()

    data.qpos[:7] = READY
    data.qpos[7:9] = 0.04
    mujoco.mj_forward(model, data)
    drive(READY, OPEN, 300)
    if frames:
        keyframes["1_start"] = frames[-1]

    block = data.body("block").xpos.copy()
    goal = data.site("target_site").xpos.copy()
    log = [f"scene: nq={model.nq} nv={model.nv} nu={model.nu}",
           f"block rest: {np.round(block, 4).tolist()}",
           f"target_site: {np.round(goal, 4).tolist()}", ""]

    q = solve_ik(data.qpos[:7], block + [0, 0, GRASP_OFFSET + 0.08]); drive(q, OPEN, 250)
    if frames: keyframes["2_reach"] = frames[-1]
    log.append(f"REACH  hand={np.round(data.body('hand').xpos, 4).tolist()}")

    q = solve_ik(data.qpos[:7], block + [0, 0, GRASP_OFFSET]); drive(q, OPEN, 350)
    log.append(f"DESCEND hand={np.round(data.body('hand').xpos, 4).tolist()}")

    drive(q, CLOSE, 300)
    if frames: keyframes["3_grasp"] = frames[-1]
    log.append(f"GRASP  fingers={np.round(data.qpos[7:9], 4).tolist()} ncon={data.ncon}")

    q = solve_ik(data.qpos[:7], block + [0, 0, GRASP_OFFSET + 0.15]); drive(q, CLOSE, 400)
    lift_z = float(data.body("block").xpos[2])
    if frames: keyframes["4_lift"] = frames[-1]
    log.append(f"LIFT   block_z={lift_z:.4f}  (dz={lift_z - block[2]:+.4f})")

    q = solve_ik(data.qpos[:7], [goal[0], goal[1], block[2] + GRASP_OFFSET + 0.15]); drive(q, CLOSE, 400)
    q = solve_ik(data.qpos[:7], [goal[0], goal[1], goal[2] + GRASP_OFFSET]); drive(q, CLOSE, 350)
    drive(q, OPEN, 250)
    if frames: keyframes["5_place"] = frames[-1]

    final = data.body("block").xpos.copy()
    xy_err = float(np.linalg.norm(final[:2] - goal[:2]))
    lifted = lift_z - block[2] > 0.10
    placed = xy_err < 0.03 and abs(final[2] - block[2]) < 0.03

    log += ["",
            f"FINAL block: {np.round(final, 4).tolist()}",
            f"place xy err: {xy_err:.4f} m",
            f"lifted: {lifted}   placed_at_target: {placed}"]
    text = "\n".join(log)
    print(text)
    (RUNS / "grasping_pipeline.txt").write_text(text + "\n")

    if renderer is not None:
        renderer.close()
        iio.imwrite(RUNS / "grasping_pipeline_video.mp4", np.stack(frames), fps=30)
        blank = np.zeros_like(keyframes["1_start"])
        order = ["1_start", "2_reach", "3_grasp", "4_lift", "5_place"]
        tiles = [keyframes.get(k, blank) for k in order] + [blank]
        grid = np.concatenate([np.concatenate(tiles[:3], 1),
                               np.concatenate(tiles[3:], 1)], 0)
        iio.imwrite(RUNS / "grasping_pipeline_keyframes.png", grid)
        print(f"[write] {RUNS / 'grasping_pipeline_video.mp4'}")
        print(f"[write] {RUNS / 'grasping_pipeline_keyframes.png'}")

    print(f"\n[{'PASS' if lifted and placed else 'FAIL'}] lifted={lifted} placed={placed}")


if __name__ == "__main__":
    main()
