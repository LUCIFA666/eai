"""4.2 — MuJoCo offscreen render of the Franka Panda over 200 frames.

The script loads a Panda model from ``reference/mujoco_menagerie`` (or
``$MUJOCO_PANDA_MODEL``), holds it at the canonical ``ready`` pose, lets
gravity drop it for 200 simulation steps and writes the resulting MP4 +
a single PNG.

Uses ``mujoco.Renderer`` (OSMesa / EGL via $MUJOCO_GL). Run with::

    MUJOCO_GL=egl python labs/04-simulation/mujoco_panda_video.py

Outputs
-------
- ``runs/04-simulation/panda_drop.mp4`` (200 frames @ 30 fps)
- ``runs/04-simulation/panda_drop.png`` (first frame)
- ``runs/04-simulation/panda_drop.txt`` (model summary + final qpos)
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

os.environ.setdefault("MUJOCO_GL", "egl")

try:
    import mujoco
except ImportError as exc:
    raise RuntimeError("mujoco missing; pip install mujoco>=3.0") from exc

try:
    import imageio.v3 as iio
except ImportError as exc:
    raise RuntimeError("imageio[ffmpeg] missing; pip install 'imageio[ffmpeg]'") from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs/04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

MODEL_OVERRIDE = os.environ.get("MUJOCO_PANDA_MODEL")
CANDIDATES = ([Path(MODEL_OVERRIDE).expanduser()] if MODEL_OVERRIDE else []) + [
    ROOT / "reference/mujoco_menagerie/franka_emika_panda/scene.xml",
    ROOT / "reference/mujoco_menagerie/franka_emika_panda/panda.xml",
]


def resolve_model() -> Path:
    for c in CANDIDATES:
        if c.exists():
            return c
    raise SystemExit(
        f"No Panda model found. Tried: {', '.join(str(c) for c in CANDIDATES)}"
    )


def public_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return "$MUJOCO_PANDA_MODEL" if MODEL_OVERRIDE else path.name


def main() -> None:
    model_path = resolve_model()
    print(f"loaded {public_path(model_path)}")
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    # Start in ready pose (first 7 are arm joints in both URDF and MJCF).
    ready = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785])
    n_arm = min(7, model.nq)
    data.qpos[:n_arm] = ready[:n_arm]
    mujoco.mj_forward(model, data)

    n_frames = 200
    width, height = 480, 320
    renderer = mujoco.Renderer(model, height=height, width=width)
    frames = []
    for _ in range(n_frames):
        mujoco.mj_step(model, data)
        renderer.update_scene(data)
        frames.append(renderer.render().copy())

    mp4 = RUNS / "panda_drop.mp4"
    png = RUNS / "panda_drop.png"
    txt = RUNS / "panda_drop.txt"
    iio.imwrite(str(mp4), np.stack(frames), fps=30, codec="libx264")
    iio.imwrite(str(png), frames[0])

    summary = (
        f"model: {model_path.name}\n"
        f"nq={model.nq}  nv={model.nv}  nu={model.nu}  nbody={model.nbody}\n"
        f"frames written: {n_frames} @ 30 fps -> {mp4.name}\n"
        f"first-frame thumb -> {png.name}\n"
        f"final qpos[:7] = {data.qpos[:7]}\n"
    )
    txt.write_text(summary, encoding="utf-8")
    print(summary)
    print(
        "wrote "
        + ", ".join(public_path(path) for path in (mp4, png, txt))
    )


if __name__ == "__main__":
    main()
