"""4.4 — Figure: multi-camera views of one scene.

Renders the Panda from three cameras (top-down, side, free) and a 3-wide
composite. Source for the multi-view figure.

Menagerie location: $MUJOCO_MENAGERIE if set, else reference/mujoco_menagerie.

Run:
    MUJOCO_GL=egl python labs/04-simulation/fig_multiview.py

Outputs:
    runs/04-simulation/fig_view_topdown.png
    runs/04-simulation/fig_view_side.png
    runs/04-simulation/fig_view_free.png
    runs/04-simulation/fig_multiview.png   (3-wide composite)
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
TMP_SCENE = PANDA_DIR / "_multiview_tmp.xml"

MULTIVIEW_XML = """<mujoco model="multiview_scene">
  <include file="scene.xml"/>
  <worldbody>
    <camera name="top_down" pos="0.4 0 1.6" xyaxes="1 0 0 0 1 0" fovy="45"/>
    <camera name="side" pos="1.5 0 0.6" xyaxes="0 1 0 0 0 1" fovy="45"/>
  </worldbody>
</mujoco>
"""


def render_camera(model, data, camera, out_path: Path) -> np.ndarray:
    with mujoco.Renderer(model, height=360, width=480) as r:
        r.update_scene(data, camera=camera)
        img = r.render().copy()
    iio.imwrite(str(out_path), img)
    print(f"[write] {out_path}  (camera={camera})")
    return img


def main() -> None:
    if not PANDA_DIR.exists():
        raise SystemExit(f"Panda dir not found at {PANDA_DIR} "
                         f"(set MUJOCO_MENAGERIE or clone into reference/)")
    TMP_SCENE.write_text(MULTIVIEW_XML)
    try:
        model = mujoco.MjModel.from_xml_path(str(TMP_SCENE))
        data = mujoco.MjData(model)
        if model.nkey > 0:
            mujoco.mj_resetDataKeyframe(model, data, 0)
        mujoco.mj_forward(model, data)

        free = render_camera(model, data, -1, RUNS / "fig_view_free.png")
        top = render_camera(model, data, "top_down", RUNS / "fig_view_topdown.png")
        side = render_camera(model, data, "side", RUNS / "fig_view_side.png")

        composite = np.concatenate([top, free, side], axis=1)
        iio.imwrite(str(RUNS / "fig_multiview.png"), composite)
        print(f"[write] {RUNS / 'fig_multiview.png'}  (composite, {composite.shape})")
    finally:
        if TMP_SCENE.exists():
            TMP_SCENE.unlink()


if __name__ == "__main__":
    main()
