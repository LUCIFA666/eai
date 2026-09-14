"""11.3 — Record CartPole rollouts as MP4 video evidence.

We use the gymnasium env for state transitions and render frames with
pure numpy + imageio (no pygame, works headless).  Same pattern that
``gymnasium.wrappers.RecordVideo`` uses internally — see comment below
for the wrapper recipe.

Run:
    python labs/11-eval/record_video.py
Outputs:
    runs/11-eval/video/success_cartpole.mp4
    runs/11-eval/video/failure_cartpole.mp4
    runs/11-eval/video/record_video_summary.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

try:
    import gymnasium as gym
except Exception as e:
    raise SystemExit(f"gymnasium import failed: {e}")


SEED = 0
FPS = 30
WIDTH, HEIGHT = 360, 240
OUT = Path("runs/11-eval/video"); OUT.mkdir(parents=True, exist_ok=True)


def render_cartpole(obs: np.ndarray, step: int, total: float) -> np.ndarray:
    """Numpy-only rasterizer: cart + pole on a white canvas."""
    x, _, theta, _ = obs
    img = np.full((HEIGHT, WIDTH, 3), 245, dtype=np.uint8)
    img[HEIGHT - 40:HEIGHT - 38, :] = 80                                  # ground
    cx = int(WIDTH / 2 + x * 60); cy = HEIGHT - 60
    img[cy - 12:cy + 12, max(0, cx - 28):min(WIDTH, cx + 28)] = (40, 70, 180)  # cart
    L = 80
    ex = int(cx + L * math.sin(theta)); ey = int(cy - L * math.cos(theta))
    n = max(abs(ex - cx), abs(ey - cy)) + 1
    for k in range(n):
        t = k / max(n - 1, 1)
        px, py = int(cx + t * (ex - cx)), int(cy + t * (ey - cy))
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                yy, xx = py + dy, px + dx
                if 0 <= yy < HEIGHT and 0 <= xx < WIDTH:
                    img[yy, xx] = (200, 60, 60)
    img[0:4, 0:int(WIDTH * min(1.0, total / 200.0))] = (40, 140, 80)
    img[6:10, 0:int(WIDTH * min(1.0, step / 200.0))] = (160, 120, 40)
    return img


def policy_balanced(obs: np.ndarray) -> int:
    """Cheap-but-stable balancing controller: push in direction of pole tilt."""
    return 1 if (obs[2] + 0.5 * obs[3]) > 0 else 0


def rollout(policy_fn, rng: np.random.Generator,
            max_steps: int = 200, label: str = "") -> tuple[list[np.ndarray], float, int]:
    env = gym.make("CartPole-v1")
    obs, _ = env.reset(seed=SEED)
    env.action_space.seed(SEED)
    frames: list[np.ndarray] = []
    total = 0.0
    steps = 0
    for _ in range(max_steps):
        frames.append(render_cartpole(obs, steps, total))
        a = int(rng.integers(0, 2)) if policy_fn is None else policy_fn(obs)
        obs, r, terminated, truncated, _ = env.step(a)
        total += float(r); steps += 1
        if terminated or truncated:
            frames.append(render_cartpole(obs, steps, total))
            break
    env.close()
    return frames, total, steps


def save_mp4(frames: list[np.ndarray], path: Path) -> None:
    imageio.mimsave(path.as_posix(), frames, fps=FPS, codec="libx264",
                    quality=8, macro_block_size=1)


# Equivalent RecordVideo recipe (needs pygame):
#   env = gym.make("CartPole-v1", render_mode="rgb_array")
#   env = gym.wrappers.RecordVideo(env, video_folder=OUT.as_posix(),
#                                  episode_trigger=lambda ep: True, name_prefix="cp")
#   ... rollout ...
#   env.close()  # close() flushes the MP4
def main() -> None:
    rng = np.random.default_rng(SEED)
    succ_frames, succ_ret, succ_steps = rollout(policy_balanced, rng, label="balanced")
    fail_frames, fail_ret, fail_steps = rollout(None, rng, label="random")
    save_mp4(succ_frames, OUT / "success_cartpole.mp4")
    save_mp4(fail_frames, OUT / "failure_cartpole.mp4")

    summary = {"seed": SEED, "fps": FPS, "frame_size_hw": [HEIGHT, WIDTH], "videos": [
        {"path": "runs/11-eval/video/success_cartpole.mp4",
         "policy": "balanced_PD", "return": succ_ret,
         "steps": succ_steps, "frames": len(succ_frames)},
        {"path": "runs/11-eval/video/failure_cartpole.mp4",
         "policy": "random", "return": fail_ret,
         "steps": fail_steps, "frames": len(fail_frames)},
    ]}
    (OUT / "record_video_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for v in summary["videos"]:
        kib = Path(v["path"]).stat().st_size / 1024
        print(f"{v['policy']:>12}  return={v['return']:>6.1f}  steps={v['steps']:>3d}  "
              f"frames={v['frames']:>3d}  size={kib:6.1f} KiB  -> {v['path']}")


if __name__ == "__main__":
    main()
