"""4.3 — MJCF / URDF model introspection.

Loads a MuJoCo model and prints its structure: bodies, joints, actuators,
sensors, geometry counts and contact pairs. Prefers ``mujoco_menagerie/
franka_emika_panda/panda.xml`` (real MJCF); ``$MUJOCO_PANDA_MODEL`` may
be used to point at another public model file.

Run:
    MUJOCO_GL=egl python labs/04-simulation/mjcf_inspect.py

Outputs:
    runs/04-simulation/mjcf_inspect.txt     (human-readable table)
    runs/04-simulation/mjcf_inspect.json    (machine-readable summary)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

os.environ.setdefault("MUJOCO_GL", "egl")

try:
    import mujoco
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("mujoco missing; install via `pip install mujoco>=3.0`") from exc


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

MODEL_OVERRIDE = os.environ.get("MUJOCO_PANDA_MODEL")
CANDIDATES = ([Path(MODEL_OVERRIDE).expanduser()] if MODEL_OVERRIDE else []) + [
    ROOT / "reference" / "mujoco_menagerie" / "franka_emika_panda" / "panda.xml",
]


def resolve_model() -> Path:
    for c in CANDIDATES:
        if c.exists():
            return c
    raise SystemExit("No model found. Tried: " + ", ".join(str(c) for c in CANDIDATES))


def public_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return "$MUJOCO_PANDA_MODEL" if MODEL_OVERRIDE else path.name


JOINT_TYPE_NAMES = {
    mujoco.mjtJoint.mjJNT_FREE: "free",
    mujoco.mjtJoint.mjJNT_BALL: "ball",
    mujoco.mjtJoint.mjJNT_SLIDE: "slide",
    mujoco.mjtJoint.mjJNT_HINGE: "hinge",
}

GEOM_TYPE_NAMES = {
    mujoco.mjtGeom.mjGEOM_PLANE: "plane",
    mujoco.mjtGeom.mjGEOM_HFIELD: "hfield",
    mujoco.mjtGeom.mjGEOM_SPHERE: "sphere",
    mujoco.mjtGeom.mjGEOM_CAPSULE: "capsule",
    mujoco.mjtGeom.mjGEOM_ELLIPSOID: "ellipsoid",
    mujoco.mjtGeom.mjGEOM_CYLINDER: "cylinder",
    mujoco.mjtGeom.mjGEOM_BOX: "box",
    mujoco.mjtGeom.mjGEOM_MESH: "mesh",
}


def main() -> None:
    model_path = resolve_model()
    print(f"[load] {public_path(model_path)}")
    model = mujoco.MjModel.from_xml_path(str(model_path))

    lines: list[str] = []
    lines.append(f"model: {model_path.name}")
    lines.append(f"  nq={model.nq}  nv={model.nv}  nu={model.nu}  na={model.na}")
    lines.append(
        f"  nbody={model.nbody}  njnt={model.njnt}  ngeom={model.ngeom}  "
        f"nsensor={model.nsensor}  ncam={model.ncam}  nlight={model.nlight}"
    )
    lines.append(f"  timestep={model.opt.timestep:.4f}  gravity={list(model.opt.gravity)}")
    lines.append("")

    lines.append("BODIES (id  name                          parent  mass  inertia)")
    for i in range(model.nbody):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i) or "<unnamed>"
        parent = model.body_parentid[i]
        mass = float(model.body_mass[i])
        inertia = [float(x) for x in model.body_inertia[i]]
        lines.append(f"  {i:3d}  {name:30s}  {parent:3d}  {mass:7.4f}  {inertia}")
    lines.append("")

    lines.append("JOINTS (id  name                          type     range[lo, hi])")
    for i in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) or "<unnamed>"
        jtype = JOINT_TYPE_NAMES.get(int(model.jnt_type[i]), "?")
        if model.jnt_limited[i]:
            lo, hi = model.jnt_range[i]
            rng = f"[{lo:+.3f}, {hi:+.3f}]"
        else:
            rng = "(unlimited)"
        lines.append(f"  {i:3d}  {name:30s}  {jtype:7s}  {rng}")
    lines.append("")

    lines.append("ACTUATORS (id  name                          ctrl_range)")
    for i in range(model.nu):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or "<unnamed>"
        lo, hi = model.actuator_ctrlrange[i]
        lines.append(f"  {i:3d}  {name:30s}  [{lo:+.3f}, {hi:+.3f}]")
    if model.nu == 0:
        lines.append("  (no actuators — URDF parses without actuators; MJCF often adds <actuator> block)")
    lines.append("")

    lines.append("SENSORS (id  name                          type)")
    for i in range(model.nsensor):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SENSOR, i) or "<unnamed>"
        lines.append(f"  {i:3d}  {name:30s}  type_id={int(model.sensor_type[i])}")
    if model.nsensor == 0:
        lines.append("  (no sensors)")
    lines.append("")

    geom_type_count: dict[str, int] = {}
    for i in range(model.ngeom):
        t = GEOM_TYPE_NAMES.get(int(model.geom_type[i]), "?")
        geom_type_count[t] = geom_type_count.get(t, 0) + 1
    lines.append("GEOM TYPE COUNTS:")
    for k in sorted(geom_type_count):
        lines.append(f"  {k:10s} = {geom_type_count[k]}")

    text = "\n".join(lines) + "\n"
    print(text)

    out_txt = RUNS / "mjcf_inspect.txt"
    out_txt.write_text(text)

    out_json = RUNS / "mjcf_inspect.json"
    out_json.write_text(
        json.dumps(
            {
                "model": model_path.name,
                "model_path": public_path(model_path),
                "nq": int(model.nq),
                "nv": int(model.nv),
                "nu": int(model.nu),
                "nbody": int(model.nbody),
                "njnt": int(model.njnt),
                "ngeom": int(model.ngeom),
                "nsensor": int(model.nsensor),
                "ncam": int(model.ncam),
                "nlight": int(model.nlight),
                "joint_types": [JOINT_TYPE_NAMES.get(int(model.jnt_type[i]), "?") for i in range(model.njnt)],
                "geom_type_counts": geom_type_count,
                "actuator_ctrlrange": model.actuator_ctrlrange.tolist() if model.nu > 0 else [],
            },
            indent=2,
        )
    )
    print(f"[write] {public_path(out_txt)}")
    print(f"[write] {public_path(out_json)}")


if __name__ == "__main__":
    main()
