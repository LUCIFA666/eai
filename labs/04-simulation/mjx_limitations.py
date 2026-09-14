"""4.7 — MJX limitation catalog.

Tries mjx.put_model on a sample of menagerie robots and records which ones MJX
rejects (and why). Reproduces the table in
section/.../07-mjx-and-gpu/04-limitations-and-warp.md.

Common failure modes in MJX (a subset of MuJoCo):
  - some collision geom pairs (e.g. cylinder) not implemented
  - some sensor / constraint / solver options outside MJX's supported subset
  - engine plugins, deformable (flex), etc.

Menagerie location: $MUJOCO_MENAGERIE if set, else reference/mujoco_menagerie
(clone it there first; see the unit's setup notes).

REQUIRES: mujoco + mujoco-mjx + a local mujoco_menagerie checkout.

Run:
    MUJOCO_MENAGERIE=/path/to/mujoco_menagerie python labs/04-simulation/mjx_limitations.py

Outputs:
    runs/04-simulation/mjx_limitations.txt
    runs/04-simulation/mjx_limitations.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

try:
    import mujoco
    from mujoco import mjx
except ImportError as exc:
    raise RuntimeError("mujoco / mujoco.mjx missing") from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

MENAGERIE = Path(os.environ.get("MUJOCO_MENAGERIE", ROOT / "reference" / "mujoco_menagerie"))

# Mix of robot types: arms, quadrupeds, humanoids, hands, sim2real testbeds.
ROBOTS = [
    "franka_emika_panda",
    "universal_robots_ur5e",
    "kuka_iiwa_14",
    "unitree_a1",
    "unitree_go2",
    "anybotics_anymal_b",
    "anybotics_anymal_c",
    "robotis_op3",
    "aloha",
    "google_robot",
    "trs_so_arm100",
]


def find_xml(robot_dir: Path) -> Path | None:
    """Return the PLAIN (non-MJX) scene xml."""
    for candidate in [robot_dir / "scene.xml", robot_dir / f"{robot_dir.name}.xml"]:
        if candidate.exists():
            return candidate
    for c in sorted(robot_dir.glob("*.xml")):
        if not c.name.startswith("mjx_"):
            return c
    return None


def try_put_model(xml_path: Path) -> dict:
    info: dict = {"xml": str(xml_path.name)}
    try:
        model = mujoco.MjModel.from_xml_path(str(xml_path))
        info.update(nq=int(model.nq), nu=int(model.nu), nbody=int(model.nbody))
    except Exception as exc:
        info["status"] = "cpu_load_failed"
        info["error"] = f"{type(exc).__name__}: {exc!s}"[:240]
        return info
    try:
        mjx.put_model(model)
        info["status"] = "mjx_ok"
    except Exception as exc:
        info["status"] = "mjx_failed"
        info["error"] = f"{type(exc).__name__}: {exc!s}"[:400]
    return info


def main() -> None:
    if not MENAGERIE.exists():
        raise SystemExit(f"mujoco_menagerie not found at {MENAGERIE} "
                         f"(set MUJOCO_MENAGERIE or clone into reference/)")

    results = []
    for robot in ROBOTS:
        rdir = MENAGERIE / robot
        if not rdir.exists():
            results.append({"robot": robot, "status": "robot_dir_missing"})
            continue
        entry = {"robot": robot}
        plain_xml = find_xml(rdir)
        if plain_xml:
            entry["plain"] = try_put_model(plain_xml)
        results.append(entry)

    lines = ["MJX put_model() outcome on menagerie robots:", ""]
    lines.append(f"{'robot':24s}  {'status':12s}  notes")
    lines.append("-" * 80)
    for e in results:
        plain = e.get("plain", {})
        status = plain.get("status", e.get("status", "-"))
        note = plain.get("error", "")[:60] if status == "mjx_failed" else ""
        lines.append(f"{e['robot']:24s}  {status:12s}  {note}")
    text = "\n".join(lines) + "\n"
    print(text)

    (RUNS / "mjx_limitations.json").write_text(json.dumps(results, indent=2))
    (RUNS / "mjx_limitations.txt").write_text(text)
    print(f"[write] {RUNS / 'mjx_limitations.txt'}")
    print(f"[write] {RUNS / 'mjx_limitations.json'}")


if __name__ == "__main__":
    main()
