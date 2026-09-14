"""Convert the 5 dynamic-figure mp4 clips to looping GIFs (for inline auto-play in docs).

Uses ffmpeg (bundled via imageio-ffmpeg) with a generated palette for good quality /
smaller size. Run after render_dynamic_figures.py.

Run: python labs/04-simulation/mp4_to_gif.py
"""
import os
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[2]
A = str(
    ROOT
    / "section"
    / "05-simulation-and-task-modeling"
    / "02-mujoco"
    / "assets"
)
FF = imageio_ffmpeg.get_ffmpeg_exe()

# (name, fps, target_width)  -- width downscale keeps gif size in check for wide grids
JOBS = [
    ("mujoco-skeleton-fall", 15, 380),
    ("mujoco-gripper-states", 15, 360),
    ("mujoco-slope-friction", 13, 620),
    ("mujoco-dm-suite", 8, 380),
    ("mujoco-gym-envs", 9, 560),
]

for name, fps, w in JOBS:
    inp = f"{A}/{name}.mp4"
    out = f"{A}/{name}.gif"
    pal = os.path.join(tempfile.gettempdir(), f"pal_{name}.png")
    vf = f"fps={fps},scale={w}:-1:flags=lanczos"
    subprocess.run([FF, "-y", "-i", inp, "-vf", vf + ",palettegen=max_colors=128", pal],
                   check=True, capture_output=True)
    subprocess.run([FF, "-y", "-i", inp, "-i", pal, "-lavfi",
                    vf + "[x];[x][1:v]paletteuse=dither=none", out],
                   check=True, capture_output=True)
    mb = os.path.getsize(out) / 1e6
    print(f"{name}.gif  {mb:.2f} MB")
