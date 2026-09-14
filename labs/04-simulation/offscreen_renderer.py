"""4.4 — Offscreen Renderer API demo (RGB / depth / segmentation).

Backs the "离屏渲染" page. Demonstrates the correct MuJoCo 3.x Renderer API:
  - context-manager use and the update_scene -> render order
  - depth mode via enable_depth_rendering()  (render() returns (H, W) float32)
  - segmentation mode via enable_segmentation_rendering()  ((H, W, 2) int32)
  - the try/finally alternative to the with-block

Note: the Renderer constructor takes (model, height, width, max_geom,
font_scale) only; depth/segmentation are runtime MODES, not constructor kwargs.

Self-contained (inline box scene), no menagerie needed.

Run:
    MUJOCO_GL=egl python labs/04-simulation/offscreen_renderer.py

Outputs:
    runs/04-simulation/offscreen_renderer.txt
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

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

XML = """
<mujoco>
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    <geom type="plane" size="1 1 0.1" rgba=".9 0 0 1"/>
    <body pos="0 0 0.5">
      <joint type="free"/>
      <geom type="box" size=".1 .2 .3" rgba="0 .9 0 1"/>
    </body>
  </worldbody>
</mujoco>
"""


def main() -> None:
    model = mujoco.MjModel.from_xml_string(XML)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    width, height = 320, 240
    lines: list[str] = []

    # ---- RGB via with-block ----
    with mujoco.Renderer(model, height=height, width=width) as r:
        r.update_scene(data)
        rgb = r.render()
        lines.append(f"RGB: shape={rgb.shape} dtype={rgb.dtype} "
                     f"min={rgb.min()} max={rgb.max()}")

        # ---- depth mode ----
        r.enable_depth_rendering()
        r.update_scene(data)
        depth = r.render()
        lines.append(f"depth: shape={depth.shape} dtype={depth.dtype} "
                     f"min={depth.min():.3f} max={depth.max():.3f} (meters)")
        r.disable_depth_rendering()

        # ---- segmentation mode ----
        r.enable_segmentation_rendering()
        r.update_scene(data)
        seg = r.render()
        lines.append(f"seg: shape={seg.shape} dtype={seg.dtype} "
                     f"unique_obj_ids={np.unique(seg[:, :, 0]).tolist()}")
        r.disable_segmentation_rendering()

    # ---- try/finally alternative ----
    r = mujoco.Renderer(model, height=height, width=width)
    try:
        r.update_scene(data)
        lines.append(f"try/finally RGB: shape={r.render().shape}")
    finally:
        r.close()

    # ---- multi-frame loop ----
    frames = []
    with mujoco.Renderer(model, height=height, width=width) as r:
        for _ in range(10):
            mujoco.mj_step(model, data)
            r.update_scene(data)
            frames.append(r.render())
    lines.append(f"multi-frame: rendered {len(frames)} frames, each {frames[0].shape}")

    text = "\n".join(lines)
    print(text)
    (RUNS / "offscreen_renderer.txt").write_text(text + "\n")
    print("\n[OK] RGB / depth / segmentation modes + with-block + try/finally verified.")


if __name__ == "__main__":
    main()
