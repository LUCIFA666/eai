"""4.2 — Figure: coordinate frames (xyz = RGB).

Renders the Panda with per-body frame axes, and with only the world frame.
Source for the coordinate-frames figure in the modeling chapter.

Menagerie location: $MUJOCO_MENAGERIE if set, else reference/mujoco_menagerie.

Run:
    MUJOCO_GL=egl python labs/04-simulation/fig_coordinate_frames.py

Outputs:
    runs/04-simulation/fig_coord_body_frames.png
    runs/04-simulation/fig_coord_world_frame.png
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


def render_with_frame(frame_type: int, out_path: Path) -> None:
    model = mujoco.MjModel.from_xml_path(str(PANDA_SCENE))
    data = mujoco.MjData(model)
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)

    opt = mujoco.MjvOption()
    mujoco.mjv_defaultOption(opt)
    opt.frame = frame_type

    with mujoco.Renderer(model, height=480, width=640) as r:
        r.update_scene(data, camera=-1, scene_option=opt)
        img = r.render()
    iio.imwrite(str(out_path), img)
    print(f"[write] {out_path}  (frame={frame_type})")


def main() -> None:
    if not PANDA_SCENE.exists():
        raise SystemExit(f"Panda scene not found at {PANDA_SCENE} "
                         f"(set MUJOCO_MENAGERIE or clone into reference/)")
    render_with_frame(mujoco.mjtFrame.mjFRAME_BODY, RUNS / "fig_coord_body_frames.png")
    render_with_frame(mujoco.mjtFrame.mjFRAME_WORLD, RUNS / "fig_coord_world_frame.png")
    print("\nConvention: x=red, y=green, z=blue; z is up (gravity = [0, 0, -9.81]).")


if __name__ == "__main__":
    main()
