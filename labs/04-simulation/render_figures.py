"""Batch-generate the MuJoCo render figures for the MuJoCo unit.

Run:
  MUJOCO_GL=egl MUJOCO_MENAGERIE=/path/to/mujoco_menagerie \
    python labs/04-simulation/render_figures.py

Every figure is wrapped in try/except so one failure does not abort the rest;
a manifest of produced files is printed at the end. Output goes to the unit's
shared assets dir with the `mujoco-` prefix.
"""
import os, glob, traceback
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
import numpy as np
import mujoco
import imageio.v2 as imageio

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
DONE, FAIL = [], []

# ----------------------------------------------------------------------------- helpers
def free_cam(model, lookat=None, dist=None, dist_scale=2.2, az=135, el=-20):
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = model.stat.center if lookat is None else lookat
    cam.distance = dist if dist is not None else dist_scale * model.stat.extent
    cam.azimuth, cam.elevation = az, el
    return cam

def render(model, data, cam=None, w=640, h=480, flags=None):
    with mujoco.Renderer(model, h, w) as r:
        opt = mujoco.MjvOption()
        if flags:
            for f, v in flags.items():
                opt.flags[f] = v
        if cam is None:
            r.update_scene(data, scene_option=opt)
        else:
            r.update_scene(data, camera=cam, scene_option=opt)
        return r.render().copy()

def resize(img, h, w):
    H, W = img.shape[:2]
    yi = (np.arange(h) * H // h).clip(0, H - 1)
    xi = (np.arange(w) * W // w).clip(0, W - 1)
    return img[yi][:, xi]

def grid(images, cols, h=300, w=300, pad=8, bg=255):
    imgs = [resize(im, h, w) for im in images]
    rows = (len(imgs) + cols - 1) // cols
    canvas = np.full((rows * h + (rows + 1) * pad, cols * w + (cols + 1) * pad, 3), bg, np.uint8)
    for i, im in enumerate(imgs):
        r, c = divmod(i, cols)
        y, x = pad + r * (h + pad), pad + c * (w + pad)
        canvas[y:y + h, x:x + w] = im
    return canvas

def save(name, arr):
    p = os.path.join(ASSETS, name)
    imageio.imwrite(p, arr)
    DONE.append(name)
    print("OK  ", name, arr.shape)

def save_mp4(name, frames, fps=30):
    p = os.path.join(ASSETS, name)
    imageio.mimsave(p, frames, fps=fps)
    DONE.append(name)
    print("OK  ", name, f"{len(frames)} frames")

def load_men(subdir, prefer="scene.xml"):
    base = f"{MEN}/{subdir}"
    cands = [os.path.join(base, prefer), os.path.join(base, subdir.split('/')[-1] + ".xml")]
    for p in cands:
        if os.path.exists(p):
            return mujoco.MjModel.from_xml_path(p)
    xmls = [x for x in glob.glob(base + "/*.xml") if "mjx" not in os.path.basename(x).lower()]
    return mujoco.MjModel.from_xml_path(sorted(xmls)[0])

def settle(model, data, n=0):
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    for _ in range(n):
        mujoco.mj_step(model, data)

def shot(subdir, az=135, el=-20, dist_scale=2.2, n=0, w=480, h=480):
    m = load_men(subdir)
    d = mujoco.MjData(m)
    settle(m, d, n)
    return render(m, d, free_cam(m, az=az, el=el, dist_scale=dist_scale), w, h)

def fig(fn):
    try:
        fn()
    except Exception as e:
        FAIL.append((fn.__name__, str(e)))
        print("FAIL", fn.__name__, "->", repr(e))
        traceback.print_exc()

# ----------------------------------------------------------------------------- figures
def f_gallery():
    panels = []
    for sub, az, el, ds in [("franka_emika_panda", 135, -20, 1.8),
                            ("unitree_go2", 120, -10, 1.6),
                            ("robotis_op3", 120, -10, 1.5),
                            ("aloha", 135, -25, 1.6)]:
        panels.append(shot(sub, az=az, el=el, dist_scale=ds))
    save("mujoco-gallery.png", grid(panels, 2, 360, 360))

def f_skeleton_fall():
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
    cam = free_cam(m, lookat=[0, 0, 0.5], dist=3.0, az=130, el=-15)
    frames, targets = [], {0, 45, 95}
    for i in range(96):
        if i in targets:
            frames.append(render(m, d, cam, 380, 420))
        mujoco.mj_step(m, d)
    save("mujoco-skeleton-fall.png", grid(frames, 3, 420, 380))

def f_default_colors():
    xml = """
    <mujoco>
      <visual><global offwidth="800" offheight="500"/></visual>
      <default class="main"><geom rgba="1 0 0 1"/>
        <default class="sub"><geom rgba="0 1 0 1"/></default>
      </default>
      <worldbody>
        <light pos="0 -1 2" dir="0 0.4 -1" diffuse="0.8 0.8 0.8"/>
        <geom type="plane" size="3 3 0.1" rgba="0.85 0.85 0.85 1"/>
        <geom class="main" type="box" pos="-0.6 0 0.18" size="0.13 0.13 0.13"/>
        <body childclass="sub">
          <geom type="ellipsoid" pos="-0.2 0 0.18" size="0.12 0.1 0.16"/>
          <geom type="sphere" pos="0.2 0 0.18" size="0.14" rgba="0 0 1 1"/>
          <geom class="main" type="cylinder" pos="0.6 0 0.18" size="0.1 0.16"/>
        </body>
      </worldbody>
    </mujoco>"""
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    cam = free_cam(m, lookat=[0, 0, 0.18], dist=2.1, az=90, el=-12)
    save("mujoco-default-colors.png", render(m, d, cam, 760, 360))

def f_one_model_two_data():
    m = load_men("franka_emika_panda")
    d = mujoco.MjData(m)
    settle(m, d)
    a = render(m, d, free_cam(m, az=135, el=-20, dist_scale=1.8), 460, 460)
    d.qpos[:7] = [0.8, -0.4, 0.3, -1.2, 0.5, 1.0, -0.6]
    mujoco.mj_forward(m, d)
    b = render(m, d, free_cam(m, az=135, el=-20, dist_scale=1.8), 460, 460)
    save("mujoco-one-model-two-data.png", grid([a, b], 2, 420, 420))

def f_keyframe_home():
    m = load_men("franka_emika_panda")
    d = mujoco.MjData(m)
    d.qpos[:] = 0
    mujoco.mj_forward(m, d)
    zero = render(m, d, free_cam(m, az=135, el=-20, dist_scale=1.8), 460, 460)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    home = render(m, d, free_cam(m, az=135, el=-20, dist_scale=1.8), 460, 460)
    save("mujoco-keyframe-home.png", grid([zero, home], 2, 420, 420))

def f_ur5e():
    save("mujoco-ur5e.png", shot("universal_robots_ur5e", az=140, el=-20, dist_scale=1.7, w=520, h=460))

def f_slope_friction():
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
        for _ in range(520):  # mu=0.1 on 20 deg slides downhill; mu=1.0 stays put
            mujoco.mj_step(m, d)
        cam = free_cam(m, lookat=[0.0, 0, -0.05], dist=3.3, az=90, el=-12)
        return render(m, d, cam, 470, 420)
    lo, hi = run(0.1), run(1.0)
    save("mujoco-slope-friction.png", grid([lo, hi], 2, 420, 470))

def f_servo_pendulum():
    xml = """
    <mujoco><option gravity="0 0 0"/>
      <worldbody>
        <light pos="0 -1 2" dir="0 0.4 -1" diffuse="0.8 0.8 0.8"/>
        <geom type="plane" size="1 1 0.1" pos="0 0 -0.4" rgba="0.85 0.85 0.85 1"/>
        <body><joint name="hinge" type="hinge" axis="0 0 1"/>
          <geom type="capsule" size="0.03" fromto="0 0 0 0.3 0 0" rgba="0.8 0.2 0.2 1"/>
        </body>
      </worldbody>
      <actuator><position name="servo" joint="hinge" kp="20" kv="2" ctrlrange="-3.14 3.14"/></actuator>
    </mujoco>"""
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    d.ctrl[0] = 1.0
    cam = free_cam(m, lookat=[0.1, 0, 0], dist=1.0, az=90, el=-80)
    frames = []
    with mujoco.Renderer(m, 360, 360) as r:
        for i in range(220):
            mujoco.mj_step(m, d)
            if i % 2 == 0:
                r.update_scene(d, camera=cam)
                frames.append(r.render().copy())
    save_mp4("mujoco-servo-pendulum.mp4", frames, fps=30)

def f_contact_viz():
    xml = """
    <mujoco><option timestep="0.002"/>
      <visual><scale contactwidth="0.05" contactheight="0.03" forcewidth="0.03"/>
        <map force="0.05"/></visual>
      <worldbody>
        <light pos="0 -1 2" dir="0 0.4 -1" diffuse="0.8 0.8 0.8"/>
        <geom type="plane" size="1 1 0.1" rgba="0.85 0.85 0.85 1"/>
        <body pos="0 0 0.08"><freejoint/>
          <geom type="box" size="0.08 0.08 0.08" rgba="0.2 0.6 1 1"/>
        </body>
      </worldbody>
    </mujoco>"""
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    for _ in range(400):
        mujoco.mj_step(m, d)
    cam = free_cam(m, lookat=[0, 0, 0.05], dist=0.7, az=120, el=-18)
    flags = {mujoco.mjtVisFlag.mjVIS_CONTACTPOINT: 1,
             mujoco.mjtVisFlag.mjVIS_CONTACTFORCE: 1}
    save("mujoco-contact-viz.png", render(m, d, cam, 560, 460, flags))

def f_rgb_depth_seg():
    m = load_men("franka_emika_panda")
    d = mujoco.MjData(m)
    settle(m, d)
    cam = free_cam(m, az=135, el=-20, dist_scale=1.7)
    with mujoco.Renderer(m, 460, 560) as r:
        r.update_scene(d, camera=cam)
        rgb = r.render().copy()
        r.enable_depth_rendering(); r.update_scene(d, camera=cam)
        dep = r.render().copy(); r.disable_depth_rendering()
        r.enable_segmentation_rendering(); r.update_scene(d, camera=cam)
        seg = r.render().copy(); r.disable_segmentation_rendering()
    valid = dep[np.isfinite(dep)]
    dmax = np.percentile(valid, 95) if valid.size else 1.0
    dn = np.clip(1.0 - dep / max(dmax, 1e-6), 0, 1)
    dep_img = (np.stack([dn, dn, dn], -1) * 255).astype(np.uint8)
    ids = seg[:, :, 0]
    rng = np.random.default_rng(0)
    palette = rng.integers(40, 235, size=(int(ids.max()) + 2, 3), dtype=np.int32)
    seg_img = np.zeros((*ids.shape, 3), np.uint8)
    mask = ids >= 0
    seg_img[mask] = palette[ids[mask]]
    save("mujoco-rgb-depth-seg.png", grid([rgb, dep_img, seg_img], 3, 380, 460))

def f_dm_suite_grid():
    from dm_control import suite
    panels = []
    for dom, task in [("cartpole", "swingup"), ("walker", "walk"),
                      ("cheetah", "run"), ("humanoid", "stand")]:
        env = suite.load(dom, task)
        env.reset()
        for _ in range(5):
            env.step(np.zeros(env.action_spec().shape))
        panels.append(env.physics.render(360, 360, camera_id=0))
    save("mujoco-dm-suite-grid.png", grid(panels, 2, 340, 340))

def f_gym_envs_grid():
    import gymnasium as gym
    panels = []
    for name in ["Ant-v5", "HalfCheetah-v5", "Hopper-v5"]:
        e = gym.make(name, render_mode="rgb_array")
        e.reset(seed=0)
        panels.append(np.asarray(e.render()))
        e.close()
    save("mujoco-gym-envs-grid.png", grid(panels, 3, 340, 340))

def _grasp_model(arm_ready=True):
    wrapper = f"""
    <mujoco model="grasp">
      <include file="scene.xml"/>
      <worldbody>
        <body name="table" pos="0.4 0 0.2"><geom name="t" type="box" size="0.3 0.4 0.2" rgba="0.6 0.42 0.25 1"/></body>
        <body name="block" pos="0.4 0 0.45"><freejoint/>
          <geom name="blk" type="box" size="0.03 0.03 0.03" mass="0.05" rgba="0.2 0.6 1 1"/></body>
        <site name="target" pos="0.4 0.2 0.41" size="0.018" rgba="0 1 0 0.6"/>
        <camera name="top" pos="0.4 0 1.35" xyaxes="1 0 0 0 1 0" fovy="42"/>
        <camera name="side" pos="1.25 -0.55 0.72" xyaxes="0.4 0.92 0 -0.25 0.11 0.96" fovy="42"/>
      </worldbody>
    </mujoco>"""
    pd = f"{MEN}/franka_emika_panda"
    tmp = os.path.join(pd, "_fig_grasp_tmp.xml")
    with open(tmp, "w") as f:
        f.write(wrapper)
    try:
        m = mujoco.MjModel.from_xml_path(tmp)
    finally:
        os.remove(tmp)
    d = mujoco.MjData(m)
    if arm_ready:
        d.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
        d.qpos[7:9] = 0.04
    mujoco.mj_forward(m, d)
    for _ in range(250):
        d.ctrl[:7] = d.qpos[:7]
        if m.nu >= 8:
            d.ctrl[7] = 255
        mujoco.mj_step(m, d)
    return m, d

def f_grasp_scene():
    m, d = _grasp_model()
    top = render(m, d, "top", 480, 440)
    side = render(m, d, "side", 480, 440)
    save("mujoco-grasp-scene.png", grid([top, side], 2, 440, 480))

def f_gripper_states():
    m = load_men("franka_emika_panda")
    panels = []
    for c in (255, 128, 0):  # ctrl -> finger gap 0.08 / 0.04 / 0.0 m
        d = mujoco.MjData(m)
        mujoco.mj_resetDataKeyframe(m, d, 0)
        for _ in range(400):
            d.ctrl[:7] = d.qpos[:7]
            d.ctrl[7] = c
            mujoco.mj_step(m, d)
        hand = d.body("hand").xpos.copy(); hand[2] -= 0.04
        cam = free_cam(m, lookat=hand, dist=0.34, az=90, el=-8)
        panels.append(render(m, d, cam, 400, 420))
    save("mujoco-gripper-states.png", grid(panels, 3, 400, 380))

def f_many_envs():
    m = load_men("unitree_go2")
    panels = []
    rng = np.random.default_rng(1)
    for k in range(16):
        d = mujoco.MjData(m)
        if m.nkey > 0:
            mujoco.mj_resetDataKeyframe(m, d, 0)
        d.qpos[7:] += rng.uniform(-0.25, 0.25, size=d.qpos[7:].shape)
        mujoco.mj_forward(m, d)
        cam = free_cam(m, az=110 + rng.uniform(-15, 15), el=-12, dist_scale=1.7)
        panels.append(render(m, d, cam, 220, 220))
    save("mujoco-many-envs-grid.png", grid(panels, 4, 200, 200, pad=4))

def f_domain_rand():
    rng = np.random.default_rng(3)
    panels = []
    for _ in range(6):
        s = rng.uniform(0.04, 0.09, 3)
        col = rng.uniform(0.2, 0.9, 3)
        xml = f"""
        <mujoco>
          <worldbody>
            <light pos="0 -1 2" dir="0 0.4 -1" diffuse="0.8 0.8 0.8"/>
            <geom type="plane" size="1 1 0.1" rgba="0.85 0.85 0.85 1"/>
            <body pos="0 0 {s[2]+0.02}"><freejoint/>
              <geom type="box" size="{s[0]} {s[1]} {s[2]}" rgba="{col[0]} {col[1]} {col[2]} 1"/>
            </body>
          </worldbody>
        </mujoco>"""
        m = mujoco.MjModel.from_xml_string(xml)
        d = mujoco.MjData(m)
        mujoco.mj_forward(m, d)
        for _ in range(60):
            mujoco.mj_step(m, d)
        cam = free_cam(m, lookat=[0, 0, 0.05], dist=0.6, az=120, el=-18)
        panels.append(render(m, d, cam, 240, 240))
    save("mujoco-domain-rand-grid.png", grid(panels, 3, 230, 230))

# skeleton-fall / slope-friction / gripper-states / dm-suite / gym-envs are now animated
# (gif): generated by render_dynamic_figures.py + mp4_to_gif.py, not here.
for f in [f_gallery, f_default_colors, f_one_model_two_data,
          f_keyframe_home, f_ur5e, f_servo_pendulum,
          f_contact_viz, f_rgb_depth_seg,
          f_grasp_scene, f_many_envs, f_domain_rand]:
    fig(f)

print("\n==== MANIFEST ====")
print("DONE:", len(DONE))
for n in DONE:
    print("  ", n)
print("FAIL:", len(FAIL))
for n, e in FAIL:
    print("  ", n, "->", e)
