"""4.2 — Figure: visual vs collision geoms.

Renders the Panda twice, toggling geom groups: visual meshes (group 2) vs
collision geoms (group 3). Source for the visual/collision figure.

Menagerie location: $MUJOCO_MENAGERIE if set, else reference/mujoco_menagerie.

Run:
    MUJOCO_GL=egl python labs/04-simulation/fig_visual_vs_collision.py

Outputs:
    runs/04-simulation/fig_panda_visual.png
    runs/04-simulation/fig_panda_collision.png
"""
from __future__ import annotations

import os
from pathlib import Path

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
PANDA_SCENE = MENAGERIE / "franka_emika_panda" / "scene.xml"


def render_with_groups(visible_groups: list[int], out_path: Path) -> None:
    model = mujoco.MjModel.from_xml_path(str(PANDA_SCENE))
    data = mujoco.MjData(model)
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)

    opt = mujoco.MjvOption()
    mujoco.mjv_defaultOption(opt)
    for i in range(6):
        opt.geomgroup[i] = 0
    for g in visible_groups:
        opt.geomgroup[g] = 1

    with mujoco.Renderer(model, height=480, width=640) as r:
        r.update_scene(data, camera=-1, scene_option=opt)
        img = r.render()
    iio.imwrite(str(out_path), img)
    print(f"[write] {out_path}  (groups visible: {visible_groups})")


def main() -> None:
    if not PANDA_SCENE.exists():
        raise SystemExit(f"Panda scene not found at {PANDA_SCENE} "
                         f"(set MUJOCO_MENAGERIE or clone into reference/)")
    render_with_groups([0, 2], RUNS / "fig_panda_visual.png")     # visual = group 2
    render_with_groups([0, 3], RUNS / "fig_panda_collision.png")  # collision = group 3
    print("\nvisual geoms = decorative meshes (group 2); collision geoms (group 3) "
          "are simplified shapes used for contact.")


if __name__ == "__main__":
    main()
