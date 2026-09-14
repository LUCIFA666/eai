"""Generate animated (mp4) versions of figures whose subject is inherently dynamic.

Replaces 5 static stills with short looping clips:
  mujoco-dm-suite.mp4       (4 dm_control tasks moving)        <- was mujoco-dm-suite-grid.png
  mujoco-gym-envs.mp4       (3 gymnasium MuJoCo envs moving)   <- was mujoco-gym-envs-grid.png
  mujoco-slope-friction.mp4 (low vs high friction sliding)     <- was mujoco-slope-friction.png
  mujoco-skeleton-fall.mp4  (free-joint box falling)           <- was mujoco-skeleton-fall.png
  mujoco-gripper-states.mp4 (gripper opening/closing)          <- was mujoco-gripper-states.png

Locomotion tasks use small sinusoidal actions (not random, not trained): the body
moves visibly without violent flailing. Honest caveat goes in the page captions.

Run: MUJOCO_GL=egl MUJOCO_MENAGERIE=/path/to/mujoco_menagerie \
  python labs/04-simulation/render_dynamic_figures.py
"""
import os, traceback
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
MEN = os.environ.get(
    "MUJOCO_MENAGERIE", str(ROOT / "reference" / "mujoco_menagerie")
)
ASSETS = str(
    ROOT
    / "section"
    / "05-simulation-and-task-modeling"
    / "02-mujoco"
    / "assets"
)
os.makedirs(ASSETS, exist_ok=True)
try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
except Exception:
    FONT = ImageFont.load_default()
DONE, FAIL = [], []


def resize(img, h, w):
    img = np.asarray(img)
    H, W = img.shape[:2]
    yi = (np.arange(h) * H // h).clip(0, H - 1)
    xi = (np.arange(w) * W // w).clip(0, W - 1)
    return img[yi][:, xi]


def save_tiled(panel_frames, labels, cols, h, w, name, fps=25, pad=8):
    n = min(len(f) for f in panel_frames)
    rows = (len(panel_frames) + cols - 1) // cols
    out = []
    for k in range(n):
        canvas = np.full((rows * h + (rows + 1) * pad, cols * w + (cols + 1) * pad, 3), 255, np.uint8)
        for j, frs in enumerate(panel_frames):
            r, c = divmod(j, cols)
            y, x = pad + r * (h + pad), pad + c * (w + pad)
            canvas[y:y + h, x:x + w] = resize(frs[k], h, w)
        im = Image.fromarray(canvas)
        dr = ImageDraw.Draw(im)
        for j, text in enumerate(labels):
            r, c = divmod(j, cols)
            x, y = pad + c * (w + pad) + 6, pad + r * (h + pad) + 5
            box = dr.textbbox((x, y), text, font=FONT)
            dr.rectangle([box[0] - 4, box[1] - 2, box[2] + 4, box[3] + 2], fill=(0, 0, 0))
            dr.text((x, y), text, fill=(255, 255, 255), font=FONT)
        out.append(np.array(im))
    imageio.mimsave(os.path.join(ASSETS, name), out, fps=fps)
    DONE.append(name)
    print("OK", name, len(out), "frames", out[0].shape)


def save_single(frames, name, fps=25):
    imageio.mimsave(os.path.join(ASSETS, name), frames, fps=fps)
    DONE.append(name)
    print("OK", name, len(frames), "frames", frames[0].shape)


def free_cam(model, lookat, dist, az, el):
    c = mujoco.MjvCamera()
    c.type = mujoco.mjtCamera.mjCAMERA_FREE
    c.lookat[:] = lookat
    c.distance = dist
    c.azimuth, c.elevation = az, el
    return c


def fig(fn):
    try:
        fn()
    except Exception as e:
        FAIL.append((fn.__name__, str(e)))
        print("FAIL", fn.__name__, "->", repr(e))
        traceback.print_exc()


# ----------------------------------------------------------------- dm_control suite
def f_dm():
    from dm_control import suite
    tasks = [("cartpole", "swingup"), ("walker", "walk"), ("cheetah", "run"), ("humanoid", "stand")]
    labels = ["cartpole", "walker", "cheetah", "humanoid"]
    panels = []
    for dom, tk in tasks:
        env = suite.load(dom, tk)
        env.reset()
        adim = env.action_spec().shape[0]
        ph = np.linspace(0, 4, adim)
        frames = []
        for i in range(110):
            t = i * 0.05
            act = 0.45 * np.sin(2 * np.pi * 0.7 * t + ph)
            env.step(act)
            frames.append(env.physics.render(260, 260, camera_id=0))
        panels.append(frames)
    save_tiled(panels, labels, 2, 250, 250, "mujoco-dm-suite.mp4", fps=25)


# ----------------------------------------------------------------- gymnasium envs
def f_gym():
    import gymnasium as gym
    names = ["Ant-v5", "HalfCheetah-v5", "Hopper-v5"]
    panels = []
    for nm in names:
        e = gym.make(nm, render_mode="rgb_array")
        e.reset(seed=0)
        adim = e.action_space.shape[0]
        ph = np.linspace(0, 4, adim)
        frames = []
        for i in range(110):
            t = i * 0.05
            act = (0.5 * np.sin(2 * np.pi * 1.0 * t + ph)).astype(np.float32)
            _, _, term, trunc, _ = e.step(act)
            frames.append(np.asarray(e.render()))
            if term or trunc:
                e.reset()
        e.close()
        panels.append(frames)
    save_tiled(panels, ["Ant", "HalfCheetah", "Hopper"], 3, 250, 250, "mujoco-gym-envs.mp4", fps=25)


# ----------------------------------------------------------------- slope friction
def f_slope():
    def run(fric):
        xml = f"""
        <mujoco><compiler angle="degree"/><option timestep="0.002"/>
          <default><geom friction="{fric} 0.005 0.0001"/></default>
          <worldbody>
            <light pos="0 -1 3" dir="0 0.3 -1" diffuse="0.9 0.9 0.9"/>
            <geom type="plane" size="1.5 0.6 0.1" euler="0 20 0" rgba="0.80 0.55 0.35 1"/>
            <body pos="-0.7 0 0.75"><freejoint/>
              <geom type="box" size="0.07 0.07 0.07" rgba="0.2 0.55 1 1"/>
            </body>
          </worldbody>
        </mujoco>"""
        m = mujoco.MjModel.from_xml_string(xml)
        d = mujoco.MjData(m)
        mujoco.mj_forward(m, d)
        cam = free_cam(m, [0.0, 0, -0.05], 3.3, 90, -12)
        frames = []
        with mujoco.Renderer(m, 300, 360) as r:
            for i in range(620):
                mujoco.mj_step(m, d)
                if i % 6 == 0:
                    r.update_scene(d, camera=cam)
                    frames.append(r.render().copy())
        return frames
    save_tiled([run(0.1), run(1.0)],
               ["mu=0.1 (low friction)", "mu=1.0 (high friction)"],
               2, 300, 360, "mujoco-slope-friction.mp4", fps=25)


# ----------------------------------------------------------------- skeleton fall
def f_skeleton():
    xml = """
    <mujoco><option timestep="0.005"/>
      <worldbody>
        <light pos="0 0 3" dir="0 0 -1" diffuse="0.7 0.7 0.7"/>
        <geom type="plane" size="2 2 0.1" rgba="0.8 0.4 0.4 1"/>
        <body pos="0 0 1"><freejoint/>
          <geom type="box" size="0.1 0.2 0.3" rgba="0.2 0.8 0.2 1"/>
        </body>
      </worldbody>
    </mujoco>"""
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    cam = free_cam(m, [0, 0, 0.5], 3.0, 130, -12)
    frames = []
    with mujoco.Renderer(m, 380, 460) as r:
        for i in range(150):
            mujoco.mj_step(m, d)
            if i % 2 == 0:
                r.update_scene(d, camera=cam)
                frames.append(r.render().copy())
    save_single(frames, "mujoco-skeleton-fall.mp4", fps=25)


# ----------------------------------------------------------------- gripper open/close
def f_gripper():
    m = mujoco.MjModel.from_xml_path(MEN + "/franka_emika_panda/scene.xml")
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)   # update derived xpos before reading hand position
    arm = d.qpos[:7].copy()
    hand = d.body("hand").xpos.copy(); hand[2] -= 0.05
    cam = free_cam(m, hand, 0.4, 90, -12)
    # ctrl[7]: 255 -> 0 (close) -> 255 (open), looped feel
    seq = np.concatenate([np.linspace(255, 0, 250), np.linspace(0, 255, 250)])
    frames = []
    with mujoco.Renderer(m, 360, 380) as r:
        for k, cmd in enumerate(seq):
            d.ctrl[:7] = arm
            d.ctrl[7] = cmd
            mujoco.mj_step(m, d)
            if k % 10 == 0:
                r.update_scene(d, camera=cam)
                frames.append(r.render().copy())
    save_single(frames, "mujoco-gripper-states.mp4", fps=25)


for f in [f_dm, f_gym, f_slope, f_skeleton, f_gripper]:
    fig(f)

print("\n==== MANIFEST ====")
print("DONE:", DONE)
print("FAIL:", FAIL)
