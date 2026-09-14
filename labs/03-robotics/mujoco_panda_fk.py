"""3.3-3.4 — Forward kinematics on the real Franka Panda via MuJoCo.

Loads ``reference/mujoco_menagerie/franka_emika_panda/panda.xml``, sets
five canonical joint configurations, and prints the end-effector pose
computed by ``mj_kinematics``.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/03-robotics/mujoco_panda_fk.py

Outputs:
- prints a table to stdout
- writes ``runs/03-robotics/panda_fk.txt`` and ``runs/03-robotics/panda_fk.json``
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

try:
    import mujoco
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "mujoco not installed. Run: pip install mujoco>=3.0"
    ) from exc

REPO_ROOT = Path(__file__).resolve().parents[2]
PANDA_XML = REPO_ROOT / "reference/mujoco_menagerie/franka_emika_panda/panda.xml"
PANDA_URDF_FALLBACK = Path(
    "/data/rbc/curobo/src/curobo/content/assets/robot/franka_description/panda.urdf"
)

EE_BODY_CANDIDATES = [
    "attachment", "hand", "right_hand", "ee_link",
    "panda_hand", "panda_link8", "panda_link7",
]

CANONICAL_QS = [
    ("home",        np.zeros(7)),
    ("ready",       np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785])),
    ("shoulder",    np.array([0.5, -1.0,  0.3, -2.0,  0.2, 1.3, 0.0])),
    ("elbow_up",    np.array([0.0, -0.3,  0.0, -1.8,  0.0, 1.5, 0.0])),
    ("reach_forward", np.array([0.0,  0.3,  0.0, -1.0,  0.0, 1.3, 0.0])),
]


def find_ee_body(model: "mujoco.MjModel") -> int:
    """Locate the end-effector body id by trying common names."""
    for name in EE_BODY_CANDIDATES:
        bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
        if bid != -1:
            return bid
    # fall back to the last body
    return model.nbody - 1


def main() -> None:
    if PANDA_XML.exists():
        model_path = PANDA_XML
    elif PANDA_URDF_FALLBACK.exists():
        model_path = PANDA_URDF_FALLBACK
        print(
            f"NOTE: {PANDA_XML} not found; falling back to curobo Panda URDF at\n"
            f"      {PANDA_URDF_FALLBACK}. MuJoCo 3.x parses URDF directly."
        )
    else:
        raise SystemExit(
            f"Neither {PANDA_XML} nor {PANDA_URDF_FALLBACK} exists. "
            f"Clone mujoco_menagerie into reference/ or install curobo."
        )

    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    ee_bid = find_ee_body(model)
    ee_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, ee_bid)

    print(f"loaded {model_path.name}")
    print(f"  nq={model.nq}, nv={model.nv}, nu={model.nu}, ee_body={ee_name!r} id={ee_bid}")

    out_rows: list[dict[str, object]] = []
    out_txt: list[str] = []
    out_txt.append(f"{'config':<16} {'x':>7} {'y':>7} {'z':>7} {'qw':>7} {'qx':>7} {'qy':>7} {'qz':>7}")
    for name, q in CANONICAL_QS:
        # Pad if menagerie panda includes 2 finger joints (nq=9): leave gripper at 0.
        if model.nq == q.shape[0]:
            data.qpos[:] = q
        elif model.nq > q.shape[0]:
            data.qpos[:] = 0
            data.qpos[: q.shape[0]] = q
        else:
            data.qpos[:] = q[: model.nq]
        data.qvel[:] = 0
        mujoco.mj_kinematics(model, data)
        pos = data.xpos[ee_bid].copy()
        quat = data.xquat[ee_bid].copy()  # (w, x, y, z)
        out_txt.append(
            f"{name:<16} {pos[0]:>+7.3f} {pos[1]:>+7.3f} {pos[2]:>+7.3f}"
            f" {quat[0]:>+7.3f} {quat[1]:>+7.3f} {quat[2]:>+7.3f} {quat[3]:>+7.3f}"
        )
        out_rows.append(
            dict(name=name, q=q.tolist(), pos=pos.tolist(), quat=quat.tolist())
        )

    txt = "\n".join(out_txt)
    print(txt)
    runs = REPO_ROOT / "runs/03-robotics"
    try:
        runs.mkdir(parents=True, exist_ok=True)
    except OSError:
        import os, tempfile
        runs = Path(os.environ.get("TMPDIR", tempfile.gettempdir())) / "hands-on-embodied-ai-03-robotics"
        runs.mkdir(parents=True, exist_ok=True)
        print(f"[warn] runs/ is read-only; writing to {runs}")
    (runs / "panda_fk.txt").write_text(txt + "\n", encoding="utf-8")
    (runs / "panda_fk.json").write_text(
        json.dumps(
            dict(model=str(model_path.name), ee_body=ee_name, configs=out_rows),
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {runs / 'panda_fk.txt'} and {runs / 'panda_fk.json'}")


if __name__ == "__main__":
    main()
