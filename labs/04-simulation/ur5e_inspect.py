"""4.2 — UR5e model inspection.

Loads the UR5e from mujoco_menagerie and prints its size + joint table.
Backs the "动手：改一个模型" exercise (UR5e has nq=6, all hinge, no gripper),
the counterpart to mjcf_inspect.py (which inspects the Panda).

Menagerie location: $MUJOCO_MENAGERIE if set, else reference/mujoco_menagerie.

Run:
    python labs/04-simulation/ur5e_inspect.py

Outputs:
    runs/04-simulation/ur5e_inspect.txt
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    import mujoco
except ImportError as exc:
    raise RuntimeError("mujoco missing; pip install mujoco>=3.0") from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

MENAGERIE = Path(os.environ.get("MUJOCO_MENAGERIE", ROOT / "reference" / "mujoco_menagerie"))

JOINT_TYPE_NAMES = {
    mujoco.mjtJoint.mjJNT_FREE: "free",
    mujoco.mjtJoint.mjJNT_BALL: "ball",
    mujoco.mjtJoint.mjJNT_SLIDE: "slide",
    mujoco.mjtJoint.mjJNT_HINGE: "hinge",
}


def main() -> None:
    model_path = MENAGERIE / "universal_robots_ur5e" / "scene.xml"
    print(f"[load] {model_path}")
    if not model_path.exists():
        raise SystemExit(f"UR5e model not found at {model_path} "
                         f"(set MUJOCO_MENAGERIE or clone into reference/)")

    model = mujoco.MjModel.from_xml_path(str(model_path))

    lines: list[str] = []
    lines.append(f"model: {model_path.name}")
    lines.append(f"  nq={model.nq}  nv={model.nv}  nu={model.nu}  na={model.na}")
    lines.append(f"  nbody={model.nbody}  njnt={model.njnt}  ngeom={model.ngeom}")
    lines.append("")
    lines.append("JOINTS (id  name                          type)")
    for i in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) or "<unnamed>"
        jtype = JOINT_TYPE_NAMES.get(int(model.jnt_type[i]), "?")
        lines.append(f"  {i:3d}  {name:30s}  {jtype}")

    text = "\n".join(lines)
    print(text)
    (RUNS / "ur5e_inspect.txt").write_text(text + "\n")

    # Sanity checks (match the unit's UR5e numbers).
    assert model.nq == 6 and model.nv == 6 and model.nu == 6, \
        f"expected 6/6/6, got {model.nq}/{model.nv}/{model.nu}"
    joint_types = [JOINT_TYPE_NAMES.get(int(model.jnt_type[i]), "?") for i in range(model.njnt)]
    assert all(t == "hinge" for t in joint_types), f"expected all hinge, got {joint_types}"
    print("\n[OK] UR5e: nq=6, nv=6, nu=6, all hinge joints (no gripper).")


if __name__ == "__main__":
    main()
