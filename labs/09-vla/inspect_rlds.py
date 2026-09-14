"""9.8 — Static inspection of Open X-Embodiment RLDS dataset specs.

We do NOT download any TFDS data here — Open X-Embodiment full mix is
~10 TB.  This script scans the local ``reference/open_x_embodiment``
clone for any per-dataset python files / READMEs that document
observation and action shapes.  If the clone is missing we fall back
to a hard-coded mini catalog that mirrors what the upstream README at
https://robotics-transformer-x.github.io/ lists.

Run:
    python labs/09-vla/inspect_rlds.py

Outputs:
- prints a markdown-style table of dataset, robot, action_dim, obs cameras
- writes ``runs/09-vla/rlds_catalog.json``
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path("reference/open_x_embodiment")
OUT = Path("runs/09-vla/rlds_catalog.json")

# 12 datasets from the Open X-Embodiment v1 mix, picked because they cover the
# main embodiments students will see in RT-X / Octo / OpenVLA training mixes.
# Source: https://docs.google.com/spreadsheets/d/1rPBD77tk60AEIGZrGSODwyyzs5FgCU9Uz3h-3_t2A9g
# (linked from the project page) — these are *upstream documented* shapes, not
# anything inferred from a checkpoint.
FALLBACK_CATALOG = [
    {
        "name": "fractal20220817_data",
        "alias": "RT-1 / Google Robot",
        "robot": "Everyday Robots (mobile manipulator)",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["image"],
        "episodes": 73499,
    },
    {
        "name": "kuka",
        "alias": "Kuka iiwa grasping",
        "robot": "Kuka iiwa",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["image"],
        "episodes": 209880,
    },
    {
        "name": "bridge",
        "alias": "Bridge V2",
        "robot": "WidowX 250",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["image", "image_1"],
        "episodes": 60096,
    },
    {
        "name": "taco_play",
        "alias": "TACO Play",
        "robot": "Franka Panda",
        "control": "joint velocity",
        "action_dim": 7,
        "obs_cameras": ["rgb_static", "rgb_gripper"],
        "episodes": 3603,
    },
    {
        "name": "jaco_play",
        "alias": "JACO Play",
        "robot": "Kinova Jaco 2",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["image", "image_wrist"],
        "episodes": 976,
    },
    {
        "name": "berkeley_cable_routing",
        "alias": "Cable routing",
        "robot": "Franka Panda",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["image", "top_image", "wrist45_image", "wrist225_image"],
        "episodes": 1647,
    },
    {
        "name": "nyu_door_opening_surprising_effectiveness",
        "alias": "NYU door opening",
        "robot": "Hello Stretch",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["image"],
        "episodes": 435,
    },
    {
        "name": "stanford_hydra_dataset_converted_externally_to_rlds",
        "alias": "Stanford Hydra",
        "robot": "Franka Panda",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["image", "wrist_image"],
        "episodes": 570,
    },
    {
        "name": "berkeley_autolab_ur5",
        "alias": "Berkeley UR5",
        "robot": "UR5",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["image", "hand_image"],
        "episodes": 896,
    },
    {
        "name": "robo_set",
        "alias": "RoboSet",
        "robot": "Franka Panda",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["image_left", "image_right", "image_wrist", "image_top"],
        "episodes": 18250,
    },
    {
        "name": "droid",
        "alias": "DROID",
        "robot": "Franka Panda + Robotiq",
        "control": "delta EE pose",
        "action_dim": 7,
        "obs_cameras": ["exterior_image_1_left", "exterior_image_2_left", "wrist_image_left"],
        "episodes": 76000,
    },
    {
        "name": "viola",
        "alias": "VIOLA",
        "robot": "Franka Panda",
        "control": "absolute EE pose",
        "action_dim": 7,
        "obs_cameras": ["agentview_rgb", "eye_in_hand_rgb"],
        "episodes": 135,
    },
]


def _scan_local_repo() -> list[Path]:
    """Return any files in reference/open_x_embodiment that look like dataset
    descriptors (`*.py` / `*.md` / `*.json` referencing 'observation' or
    'action_dim').
    """
    if not REPO.exists():
        return []
    matches: list[Path] = []
    for ext in ("*.py", "*.md", "*.json"):
        for p in REPO.rglob(ext):
            try:
                txt = p.read_text(errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue
            if "action" in txt and ("observation" in txt or "image" in txt):
                matches.append(p)
    return matches[:20]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    local_files = _scan_local_repo()

    summary = {
        "source": "static fallback (upstream Open X-Embodiment README)",
        "local_repo_present": REPO.exists(),
        "num_local_files_with_action_obs_keywords": len(local_files),
        "local_examples": [str(p) for p in local_files[:5]],
        "datasets": FALLBACK_CATALOG,
    }
    OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print(
        f"local repo present: {summary['local_repo_present']}  "
        f"(found {len(local_files)} candidate files)"
    )
    if local_files:
        print("first few:")
        for p in local_files[:5]:
            print(f"  {p}")
    print()
    print(
        f"{'dataset':<48}  {'robot':<26}  {'a_dim':>5}  cameras"
    )
    print("-" * 120)
    for ds in FALLBACK_CATALOG:
        print(
            f"{ds['name']:<48}  {ds['robot']:<26}  {ds['action_dim']:>5}  "
            f"{','.join(ds['obs_cameras'])}"
        )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
