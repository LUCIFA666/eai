"""Generate a 3-panel side-by-side comparison video of the three actuator types.

Same single-hinge pendulum (gravity off), each driven by one actuator type with a
characteristic ctrl. Shows the qualitative difference:
  - motor    (red):   ctrl = torque        -> keeps accelerating (spins ever faster)
  - position (green): ctrl = target angle  -> settles at the target and holds
  - velocity (blue):  ctrl = target speed  -> rotates at a constant speed

Run: MUJOCO_GL=egl python labs/04-simulation/render_actuator_compare.py
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
        FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except Exception:
        FONT = ImageFont.load_default()
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

print("PIL:", HAVE_PIL)


def top_cam():
    c = mujoco.MjvCamera()
    c.type = mujoco.mjtCamera.mjCAMERA_FREE
    c.lookat[:] = [0.15, 0, 0]
    c.distance = 0.85
    c.azimuth = 90
    c.elevation = -89
    return c


def build(actuator_xml, rgba):
    xml = f"""
    <mujoco><option gravity="0 0 0"/>
      <worldbody>
        <light pos="0 0 1" dir="0 0 -1" diffuse="0.8 0.8 0.8"/>
        <geom type="plane" size="1 1 0.1" pos="0 0 -0.4" rgba="0.92 0.92 0.92 1"/>
        <body>
          <joint name="h" type="hinge" axis="0 0 1"/>
          <geom type="capsule" size="0.025" fromto="0 0 0 0.3 0 0" rgba="{rgba}"/>
          <geom type="sphere" size="0.04" rgba="0.25 0.25 0.28 1"/>
        </body>
      </worldbody>
      <actuator>{actuator_xml}</actuator>
    </mujoco>"""
    return mujoco.MjModel.from_xml_string(xml)


SPECS = [
    ("motor",    '<motor name="a" joint="h" ctrlrange="-5 5"/>',                       0.05, "0.85 0.25 0.2 1"),
    ("position", '<position name="a" joint="h" kp="20" kv="2" ctrlrange="-3.14 3.14"/>', 1.0,  "0.2 0.7 0.3 1"),
    ("velocity", '<velocity name="a" joint="h" kv="3" ctrlrange="-5 5"/>',             2.0,  "0.2 0.45 0.9 1"),
]

models = [build(a, rgba) for _, a, _, rgba in SPECS]
datas = [mujoco.MjData(m) for m in models]
for d, (_, _, c, _) in zip(datas, SPECS):
    d.ctrl[0] = c
renderers = [mujoco.Renderer(m, 240, 240) for m in models]

W = H = 240
GAP = 8
frames = []
for i in range(1500):
    for m, d in zip(models, datas):
        mujoco.mj_step(m, d)
    if i % 10 == 0:
        panels = []
        for m, d, r in zip(models, datas, renderers):
            r.update_scene(d, camera=top_cam())
            panels.append(r.render().copy())
        canvas = np.full((H + GAP * 2, W * 3 + GAP * 4, 3), 255, np.uint8)
        for j, p in enumerate(panels):
            x = GAP + j * (W + GAP)
            canvas[GAP:GAP + H, x:x + W] = p
        if HAVE_PIL:
            im = Image.fromarray(canvas)
            dr = ImageDraw.Draw(im)
            for j, (name, _, _, _) in enumerate(SPECS):
                x = GAP + j * (W + GAP) + 8
                dr.rectangle([x - 4, GAP + 4, x + 96, GAP + 28], fill=(0, 0, 0))
                dr.text((x, GAP + 6), name, fill=(255, 255, 255), font=FONT)
            canvas = np.array(im)
        frames.append(canvas)
for r in renderers:
    r.close()

out = os.path.join(ASSETS, "mujoco-actuator-compare.mp4")
imageio.mimsave(out, frames, fps=30)
print("OK actuator-compare", len(frames), "frames", frames[0].shape)
print("final  motor qvel =", round(float(datas[0].qvel[0]), 2),
      "| position qpos =", round(float(datas[1].qpos[0]), 3),
      "| velocity qvel =", round(float(datas[2].qvel[0]), 2))
