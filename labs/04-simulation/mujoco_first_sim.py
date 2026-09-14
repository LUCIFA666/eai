"""4.2 — MuJoCo first simulation.

Loads the Franka Emika Panda scene from ``reference/mujoco_menagerie``
(or ``$MUJOCO_PANDA_MODEL``), steps the physics for 200 frames with a
small sinusoidal control, and saves a deterministic MP4 plus a still PNG.
Uses the offscreen ``mujoco.Renderer`` so no DISPLAY is needed (works in
headless servers).

Run:
    MUJOCO_GL=egl python labs/04-simulation/mujoco_first_sim.py

Outputs:
    runs/04-simulation/mujoco_first_sim.mp4   (200 frames, 30 fps)
    runs/04-simulation/mujoco_first_sim.png   (first frame thumbnail)
    runs/04-simulation/mujoco_first_sim.txt   (JSON model summary)
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

try:
    import imageio.v3 as iio
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "imageio[ffmpeg] missing; install via `pip install 'imageio[ffmpeg]'`"
    ) from exc


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

MODEL_OVERRIDE = os.environ.get("MUJOCO_PANDA_MODEL")
CANDIDATES = ([Path(MODEL_OVERRIDE).expanduser()] if MODEL_OVERRIDE else []) + [
    ROOT / "reference" / "mujoco_menagerie" / "franka_emika_panda" / "scene.xml",
    ROOT / "reference" / "mujoco_menagerie" / "franka_emika_panda" / "panda.xml",
]


def resolve_model() -> Path:
    for c in CANDIDATES:
        if c.exists():
            return c
    raise SystemExit(
        "No Panda model found. Tried: " + ", ".join(str(c) for c in CANDIDATES)
    )


def public_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return "$MUJOCO_PANDA_MODEL" if MODEL_OVERRIDE else path.name


def main() -> None:
    np.random.seed(0)
    model_path = resolve_model()
    print(f"[load] {public_path(model_path)}")
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    print(f"[info] nq={model.nq} nv={model.nv} nu={model.nu} timestep={model.opt.timestep:.4f}")
    print(f"[info] bodies={model.nbody} joints={model.njnt} actuators={model.nu}")

    # Move to ready pose; first 7 entries are arm joints in both URDF and MJCF.
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    else:
        ready = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785])
        data.qpos[: min(7, model.nq)] = ready[: min(7, model.nq)]
    mujoco.mj_forward(model, data)

    # Sinusoidal control on every actuator.
    if model.nu > 0:
        ctrl_range = model.actuator_ctrlrange.copy()
        bias = 0.5 * (ctrl_range[:, 1] + ctrl_range[:, 0])
        amp = 0.15 * (ctrl_range[:, 1] - ctrl_range[:, 0])
        bias = np.where(np.isfinite(bias), bias, 0.0)
        amp = np.where(np.isfinite(amp), amp, 0.0)
    else:
        bias = amp = None

    n_frames = 200
    width, height = 640, 480
    frames: list[np.ndarray] = []
    sim_times = []
    with mujoco.Renderer(model, height=height, width=width) as renderer:
        for i in range(n_frames):
            t = i * model.opt.timestep * 5
            if model.nu > 0:
                data.ctrl[:] = bias + amp * np.sin(
                    2 * np.pi * 0.5 * np.linspace(0, 1, model.nu) + t
                )
            for _ in range(5):  # 5x physics per render frame
                mujoco.mj_step(model, data)
            renderer.update_scene(data, camera=-1)
            frames.append(renderer.render().copy())
            sim_times.append(float(data.time))

    mp4 = RUNS / "mujoco_first_sim.mp4"
    iio.imwrite(str(mp4), np.stack(frames), fps=30, codec="libx264", macro_block_size=1)
    png = RUNS / "mujoco_first_sim.png"
    iio.imwrite(str(png), frames[0])
    txt = RUNS / "mujoco_first_sim.txt"
    info = {
        "mujoco_version": mujoco.__version__,
        "model_path": public_path(model_path),
        "model_name": model_path.name,
        "nq": int(model.nq),
        "nv": int(model.nv),
        "nu": int(model.nu),
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "timestep": float(model.opt.timestep),
        "frames": len(frames),
        "wall_time_final": sim_times[-1],
        "final_qpos_head": data.qpos[: min(7, model.nq)].tolist(),
    }
    txt.write_text(json.dumps(info, indent=2))
    print(f"[write] {public_path(mp4)}  ({len(frames)} frames)")
    print(f"[write] {public_path(png)}")
    print(f"[write] {public_path(txt)}")
    print(json.dumps(info))


if __name__ == "__main__":
    main()
