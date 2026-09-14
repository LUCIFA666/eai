"""3.3 — Inspect an MJCF model: list bodies, joints, actuators, sensors.

Run:
    python labs/03-robotics/mjcf_inspect.py [path_to_xml]

Default model: ``reference/mujoco_menagerie/franka_emika_panda/panda.xml``.
Writes ``runs/03-robotics/mjcf_inspect_<model>.txt``.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import mujoco
except ImportError as exc:
    raise SystemExit("install mujoco>=3.0") from exc

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT = REPO_ROOT / "reference/mujoco_menagerie/franka_emika_panda/panda.xml"
FALLBACK = Path(
    "/data/rbc/curobo/src/curobo/content/assets/robot/franka_description/panda.urdf"
)

JNT_TYPE_NAMES = {
    mujoco.mjtJoint.mjJNT_FREE: "free",
    mujoco.mjtJoint.mjJNT_BALL: "ball",
    mujoco.mjtJoint.mjJNT_SLIDE: "slide",
    mujoco.mjtJoint.mjJNT_HINGE: "hinge",
}


def main(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"model not found: {path}")
    model = mujoco.MjModel.from_xml_path(str(path))
    out_lines = []
    out_lines.append(f"=== {path.name} ===")
    out_lines.append(f"nq={model.nq} nv={model.nv} nu={model.nu} nbody={model.nbody}")
    out_lines.append("")
    out_lines.append("Joints:")
    for i in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) or "<anon>"
        jt = model.jnt_type[i]
        lo, hi = model.jnt_range[i]
        out_lines.append(
            f"  [{i}] {name:24s} type={JNT_TYPE_NAMES.get(jt, jt)} range=[{lo:.3f}, {hi:.3f}]"
        )
    out_lines.append("")
    out_lines.append("Actuators:")
    for i in range(model.nu):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or "<anon>"
        lo, hi = model.actuator_ctrlrange[i]
        out_lines.append(f"  [{i}] {name:24s} ctrl=[{lo:.3f}, {hi:.3f}]")
    out_lines.append("")
    out_lines.append("Sensors:")
    for i in range(model.nsensor):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SENSOR, i) or "<anon>"
        out_lines.append(f"  [{i}] {name}")

    txt = "\n".join(out_lines)
    print(txt)
    out_dir = REPO_ROOT / "runs/03-robotics"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"mjcf_inspect_{path.stem}.txt").write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = Path(sys.argv[1]).expanduser()
    elif DEFAULT.exists():
        target = DEFAULT
    elif FALLBACK.exists():
        print(f"NOTE: {DEFAULT} not present; using fallback {FALLBACK}")
        target = FALLBACK
    else:
        target = DEFAULT  # will trigger informative error
    main(target)
