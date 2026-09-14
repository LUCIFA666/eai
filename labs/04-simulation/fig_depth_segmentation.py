"""4.4 — Figure: depth and segmentation rendering.

Renders the Panda as RGB, depth (meters), and segmentation (per-geom id), using
the runtime-mode API: enable_depth_rendering() / enable_segmentation_rendering().
Source for the depth/segmentation figures.

Segmentation convention: render() returns (H, W, 2) int32 where channel 0 is the
object id (geom id for a geom) and channel 1 is the object type (mjtObj; geom=5);
background pixels are (-1, -1). Color per geom id via channel 0.

Menagerie location: $MUJOCO_MENAGERIE if set, else reference/mujoco_menagerie.

Run:
    MUJOCO_GL=egl python labs/04-simulation/fig_depth_segmentation.py

Outputs:
    runs/04-simulation/fig_rgb.png
    runs/04-simulation/fig_depth.png   (normalized 8-bit; closer = brighter)
    runs/04-simulation/fig_depth.npy   (raw float32 depth, meters)
    runs/04-simulation/fig_seg.png     (per-geom id colored)
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
PANDA_SCENE = MENAGERIE / "franka_emika_panda" / "scene.xml"


def main() -> None:
    if not PANDA_SCENE.exists():
        raise SystemExit(f"Panda scene not found at {PANDA_SCENE} "
                         f"(set MUJOCO_MENAGERIE or clone into reference/)")

    model = mujoco.MjModel.from_xml_path(str(PANDA_SCENE))
    data = mujoco.MjData(model)
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)

    with mujoco.Renderer(model, height=480, width=640) as r:
        # --- RGB ---
        r.update_scene(data, camera=-1)
        rgb = r.render().copy()
        iio.imwrite(str(RUNS / "fig_rgb.png"), rgb)
        print(f"[write] fig_rgb.png  shape={rgb.shape}")

        # --- Depth (runtime mode) ---
        r.enable_depth_rendering()
        r.update_scene(data, camera=-1)
        depth = r.render().copy()                  # (H, W) float32, meters
        print(f"[depth] shape={depth.shape} min={depth.min():.3f} max={depth.max():.3f}")
        np.save(RUNS / "fig_depth.npy", depth)

        bg_threshold = float(depth.max()) * 0.99
        fg_mask = depth < bg_threshold
        if fg_mask.any():
            lo, hi = float(depth[fg_mask].min()), float(depth[fg_mask].max())
        else:
            lo, hi = float(depth.min()), float(depth.max())
        depth_norm = np.zeros_like(depth)
        depth_norm[fg_mask] = 1.0 - (depth[fg_mask] - lo) / max(hi - lo, 1e-6)
        iio.imwrite(str(RUNS / "fig_depth.png"), np.clip(depth_norm * 255, 0, 255).astype(np.uint8))
        print(f"[write] fig_depth.png  (foreground {lo:.2f}-{hi:.2f} m, bg -> black)")
        r.disable_depth_rendering()

        # --- Segmentation (runtime mode) ---
        r.enable_segmentation_rendering()
        r.update_scene(data, camera=-1)
        seg = r.render().copy()                    # (H, W, 2) int32
        geom_ids = seg[:, :, 0]
        print(f"[seg]   shape={seg.shape}  unique ids (incl. -1 bg): {np.unique(geom_ids).tolist()}")
        max_id = int(geom_ids.max())
        rng = np.random.default_rng(0)
        palette = rng.integers(60, 255, size=(max_id + 2, 3), dtype=np.uint8)
        palette[0] = (30, 30, 30)                  # background (id -1 -> row 0)
        iio.imwrite(str(RUNS / "fig_seg.png"), palette[geom_ids + 1])
        print(f"[write] fig_seg.png")
        r.disable_segmentation_rendering()


if __name__ == "__main__":
    main()
