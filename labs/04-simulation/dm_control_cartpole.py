"""4.4 — dm_control Cartpole swingup with 100-step random rollout.

Why dm_control: it ships canonical MuJoCo task suites (cartpole,
humanoid, walker, manipulator, …) without needing any external XML.
A great fallback when mujoco_menagerie clone is slow.

Run:
    python labs/04-simulation/dm_control_cartpole.py

Outputs:
- prints obs/action shape and per-step rewards
- writes runs/04-simulation/dm_cartpole.txt
- writes runs/04-simulation/dm_cartpole.mp4 (100 frames, 50 fps)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    from dm_control import suite
except ImportError as exc:
    raise RuntimeError("dm_control missing; pip install dm_control") from exc

try:
    import imageio.v3 as iio
except ImportError as exc:
    raise RuntimeError("imageio[ffmpeg] missing; pip install 'imageio[ffmpeg]'") from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs/04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)


def main() -> None:
    import os
    # Force EGL for headless rendering (no DISPLAY needed)
    os.environ.setdefault("MUJOCO_GL", "egl")

    rng = np.random.default_rng(0)
    env = suite.load(domain_name="cartpole", task_name="swingup", task_kwargs={"random": 0})

    spec = env.action_spec()
    obs_spec = env.observation_spec()

    lines = []
    lines.append(f"domain=cartpole task=swingup")
    lines.append(f"action_spec: shape={spec.shape} low={spec.minimum} high={spec.maximum}")
    obs_keys = list(obs_spec.keys())
    lines.append(f"observation keys: {obs_keys}")

    ts = env.reset()
    total_reward = 0.0
    frames = []
    rendering_ok = True
    for step in range(100):
        action = rng.uniform(spec.minimum, spec.maximum, size=spec.shape)
        ts = env.step(action)
        total_reward += float(ts.reward or 0.0)
        if rendering_ok:
            try:
                pixels = env.physics.render(height=320, width=480, camera_id=0)
                frames.append(pixels)
            except Exception as exc:
                rendering_ok = False
                lines.append(f"[render] offscreen rendering unavailable: {type(exc).__name__}; "
                             f"will report metrics only. Reason: {exc!s}"[:200])
        if step < 5 or step % 25 == 0:
            obs_dim = sum(int(np.prod(v.shape)) for v in obs_spec.values())
            lines.append(f"step={step:3d}  reward={ts.reward:.4f}  obs_dim={obs_dim}")
    lines.append(f"100-step total reward (random) = {total_reward:.3f}")

    if frames:
        mp4 = RUNS / "dm_cartpole.mp4"
        iio.imwrite(str(mp4), np.stack(frames), fps=50, codec="libx264")
        lines.append(
            f"wrote runs/04-simulation/{mp4.name} "
            f"({len(frames)} frames @ 50 fps)"
        )
    else:
        lines.append("video skipped (no OpenGL backend); metrics still verified")

    txt = "\n".join(lines)
    print(txt)
    (RUNS / "dm_cartpole.txt").write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
