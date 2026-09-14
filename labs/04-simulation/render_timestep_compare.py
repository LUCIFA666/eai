"""2-panel timestep-stability comparison video (gravity-driven box tower).

A tower of stacked free boxes settles on the ground. Only the integration timestep
differs (contact-rich scene, natural falling speed):
  - left  dt=0.002  -> the tower stands stably
  - right dt=0.040  -> the contact/integration can no longer keep up, the tower
                       wobbles and collapses (numerical instability at a too-large step)

Both panels advance over the SAME 3.0 s of simulated time, one frame every 0.02 s of
sim time, so the panels are time-synchronised.

Run: MUJOCO_GL=egl python labs/04-simulation/render_timestep_compare.py
"""
import os
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
import numpy as np
import mujoco
import imageio.v2 as imageio

ROOT = Path(__file__).resolve().parents[2]
ASSETS = str(
    ROOT
    / "section"
    / "05-simulation-and-task-modeling"
    / "02-mujoco"
    / "assets"
)
os.makedirs(ASSETS, exist_ok=True)

try:
    from PIL import Image, ImageDraw, ImageFont
    try:
        FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
    except Exception:
        FONT = ImageFont.load_default()
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

N = 8
RNG = np.random.default_rng(0)
OFFSETS = RNG.uniform(-0.003, 0.003, size=(N, 2))  # tiny seed asymmetry, same for both panels


def make_tower():
    bodies = ""
    for i in range(N):
        z = 0.04 + i * 0.084
        ox, oy = OFFSETS[i]
        t = i / (N - 1)
        rgba = f"{0.2 + 0.7 * t:.3f} {0.45:.3f} {0.9 - 0.6 * t:.3f} 1"
        bodies += (f'<body pos="{ox:.4f} {oy:.4f} {z:.3f}"><freejoint/>'
                   f'<geom type="box" size="0.04 0.04 0.04" rgba="{rgba}"/></body>')
    return ('<mujoco><option gravity="0 0 -9.81"/>'
            '<worldbody><light pos="0 -1 2" dir="0 0.4 -1" diffuse="0.85 0.85 0.85"/>'
            '<geom type="plane" size="2 2 0.1" rgba="0.9 0.9 0.9 1"/>'
            + bodies + '</worldbody></mujoco>')


def cam():
    c = mujoco.MjvCamera()
    c.type = mujoco.mjtCamera.mjCAMERA_FREE
    c.lookat[:] = [0, 0, 0.32]
    c.distance = 1.4
    c.azimuth = 135
    c.elevation = -12
    return c


def run_panel(dt, sim_time=3.0, frame_every=0.04):  # 0.04 = common multiple of both dt, keeps panels in sync
    m = mujoco.MjModel.from_xml_string(make_tower())
    d = mujoco.MjData(m)
    m.opt.timestep = dt
    mujoco.mj_forward(m, d)
    steps = int(round(sim_time / dt))
    every = max(1, int(round(frame_every / dt)))
    frames = []
    with mujoco.Renderer(m, 300, 300) as r:
        for i in range(steps):
            mujoco.mj_step(m, d)
            if i % every == 0:
                r.update_scene(d, camera=cam())
                frames.append(r.render().copy())
    return frames


left = run_panel(0.002)
right = run_panel(0.040)
n = min(len(left), len(right))
left, right = left[:n], right[:n]

GAP, H, W = 8, 300, 300
labels = ["dt = 0.002  (stable)", "dt = 0.040  (unstable)"]
panels = [left, right]
out = []
for k in range(n):
    canvas = np.full((H + GAP * 2, W * 2 + GAP * 3, 3), 255, np.uint8)
    for j, frs in enumerate(panels):
        x = GAP + j * (W + GAP)
        canvas[GAP:GAP + H, x:x + W] = frs[k]
    if HAVE_PIL:
        im = Image.fromarray(canvas)
        dr = ImageDraw.Draw(im)
        for j, text in enumerate(labels):
            x = GAP + j * (W + GAP) + 8
            dr.rectangle([x - 4, GAP + 4, x + 196, GAP + 26], fill=(0, 0, 0))
            dr.text((x, GAP + 6), text, fill=(255, 255, 255), font=FONT)
        canvas = np.array(im)
    out.append(canvas)

imageio.mimsave(os.path.join(ASSETS, "mujoco-timestep-compare.mp4"), out, fps=25)
print("OK timestep-compare", len(out), "frames", out[0].shape)
