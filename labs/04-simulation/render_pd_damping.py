"""3-panel PD damping comparison video (underdamped / critical / overdamped).

Same single-hinge rod driven by a Python PD controller toward target = 1.0 rad
(gravity off). Only Kd changes; the green reference line marks the target angle:
  - Kd=1   underdamped : overshoots past the target, then oscillates back
  - Kd=5   critical    : reaches the target fast, almost no overshoot
  - Kd=20  overdamped  : crawls toward the target slowly, never overshoots

Run: MUJOCO_GL=egl python labs/04-simulation/render_pd_damping.py
"""
import os
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
import math
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
        FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except Exception:
        FONT = ImageFont.load_default()
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

TARGET = 1.0
TX, TZ = -0.5 * math.sin(TARGET), -0.5 * math.cos(TARGET)   # target rod tip (rotation about +y)

XML = f"""
<mujoco>
  <option gravity="0 0 0"/>
  <worldbody>
    <light pos="0 -1 1" dir="0 0.5 -1" diffuse="0.85 0.85 0.85"/>
    <geom type="plane" size="1 1 0.1" pos="0 0 -0.7" rgba="0.93 0.93 0.93 1"/>
    <!-- 目标角度参考线（绿色、不参与碰撞） -->
    <geom type="capsule" size="0.012" fromto="0 0 0 {TX:.4f} 0 {TZ:.4f}"
          rgba="0.2 0.8 0.3 0.6" contype="0" conaffinity="0"/>
    <body>
      <joint name="hinge" type="hinge" axis="0 1 0"/>
      <geom type="capsule" size="0.03" fromto="0 0 0 0 0 -0.5" rgba="0.85 0.25 0.2 1"/>
      <geom type="sphere" size="0.045" rgba="0.25 0.25 0.28 1"/>
    </body>
  </worldbody>
  <actuator>
    <motor name="m" joint="hinge" ctrlrange="-50 50"/>
  </actuator>
</mujoco>"""

SPECS = [("Kd=1  underdamped", 50, 1),
         ("Kd=5  critical", 50, 5),
         ("Kd=20  overdamped", 50, 20)]


def cam():
    c = mujoco.MjvCamera()
    c.type = mujoco.mjtCamera.mjCAMERA_FREE
    c.lookat[:] = [-0.12, 0, -0.25]
    c.distance = 1.25
    c.azimuth = 90
    c.elevation = 0
    return c


def run_panel(Kp, Kd, steps=500, every=10):
    m = mujoco.MjModel.from_xml_string(XML)
    d = mujoco.MjData(m)
    frames = []
    with mujoco.Renderer(m, 280, 280) as r:
        for i in range(steps):
            e = TARGET - d.qpos[0]
            d.ctrl[0] = Kp * e - Kd * d.qvel[0]
            mujoco.mj_step(m, d)
            if i % every == 0:
                r.update_scene(d, camera=cam())
                frames.append(r.render().copy())
    return frames


panels = [run_panel(Kp, Kd) for _, Kp, Kd in SPECS]
n = min(len(p) for p in panels)
panels = [p[:n] for p in panels]

GAP, H, W = 8, 280, 280
out = []
for k in range(n):
    canvas = np.full((H + GAP * 2, W * 3 + GAP * 4, 3), 255, np.uint8)
    for j, p in enumerate(panels):
        x = GAP + j * (W + GAP)
        canvas[GAP:GAP + H, x:x + W] = p[k]
    if HAVE_PIL:
        im = Image.fromarray(canvas)
        dr = ImageDraw.Draw(im)
        for j, (text, _, _) in enumerate(SPECS):
            x = GAP + j * (W + GAP) + 8
            dr.rectangle([x - 4, GAP + 4, x + 170, GAP + 25], fill=(0, 0, 0))
            dr.text((x, GAP + 6), text, fill=(255, 255, 255), font=FONT)
        canvas = np.array(im)
    out.append(canvas)

imageio.mimsave(os.path.join(ASSETS, "mujoco-pd-damping.mp4"), out, fps=25)
print("OK pd-damping", len(out), "frames", out[0].shape)
