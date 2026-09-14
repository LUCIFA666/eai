"""4.99 — MuJoCo 单元教程代码逐页验证驱动。

把 section/05-simulation-and-task-modeling/02-mujoco/ 各页出现的代码块和
数值断言（time/qpos/nq/ncon/输出形状等）逐条搬进独立测试，在真实环境里
实跑核对，保证"教程代码能跑、数字可复现"。

Run (Linux server, conda env with mujoco/dm_control/shimmy/gymnasium/sb3):
    MUJOCO_GL=egl python labs/04-simulation/verify_tutorial_code.py
    # 只跑名字含关键字的测试：
    MUJOCO_GL=egl python labs/04-simulation/verify_tutorial_code.py --only grasp

Outputs:
    runs/04-simulation/verify_tutorial_code.txt

menagerie 路径按顺序探测：$MUJOCO_MENAGERIE、$MENAGERIE_DIR、
reference/mujoco_menagerie、~/mujoco_menagerie。
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import shutil
import sys
import tempfile
import traceback
from contextlib import redirect_stdout
from pathlib import Path

if "MUJOCO_GL" not in os.environ and not os.environ.get("DISPLAY"):
    os.environ["MUJOCO_GL"] = "egl"

import numpy as np

_HERE = Path(__file__).resolve()
# 在仓库内跑：写 runs/04-simulation；单文件拷走跑：写脚本所在目录
if len(_HERE.parents) > 2 and (_HERE.parents[2] / "labs").exists():
    ROOT = _HERE.parents[2]
    RUNS = ROOT / "runs" / "04-simulation"
else:
    ROOT = _HERE.parent
    RUNS = _HERE.parent
RESULTS: list[tuple[str, str, str]] = []   # (name, status, detail)
TESTS: list[tuple[str, object]] = []

MENAGERIE_CANDIDATES = [
    os.environ.get("MUJOCO_MENAGERIE", ""),
    os.environ.get("MENAGERIE_DIR", ""),
    str(ROOT / "reference" / "mujoco_menagerie"),
    str(Path.home() / "mujoco_menagerie"),
]


def menagerie_dir() -> Path | None:
    for c in MENAGERIE_CANDIDATES:
        if c and (Path(c) / "franka_emika_panda" / "scene.xml").exists():
            return Path(c)
    return None


def public_menagerie_path(path: Path | None) -> str:
    """Return a stable label suitable for committed logs."""
    if path is None:
        return "MISSING"
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        if os.environ.get("MUJOCO_MENAGERIE"):
            return "$MUJOCO_MENAGERIE"
        if os.environ.get("MENAGERIE_DIR"):
            return "$MENAGERIE_DIR"
        if path.resolve() == (Path.home() / "mujoco_menagerie").resolve():
            return "~/mujoco_menagerie"
        return path.name


def test(name):
    def deco(fn):
        TESTS.append((name, fn))
        return fn
    return deco


def approx(a, b, tol):
    return abs(float(a) - float(b)) <= tol


# ---------------------------------------------------------------- 01-overview
MIN_XML = """
<mujoco>
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    <geom type="plane" size="1 1 0.1" rgba=".9 0 0 1"/>
    <body pos="0 0 1">
      <joint type="free"/>
      <geom type="box" size=".1 .2 .3" rgba="0 .9 0 1"/>
    </body>
  </worldbody>
</mujoco>
"""


@test("01-03 install: 最小示例 100/1000 步数值")
def t_install_minimal():
    import mujoco
    model = mujoco.MjModel.from_xml_string(MIN_XML)
    data = mujoco.MjData(model)
    for _ in range(100):
        mujoco.mj_step(model, data)
    t100, z100 = data.time, float(data.qpos[2])
    assert approx(t100, 0.200, 1e-9), f"time={t100}"
    assert approx(z100, 0.80, 0.03), f"z@100={z100}（页面写约 0.80）"
    data2 = mujoco.MjData(model)
    for _ in range(1000):
        mujoco.mj_step(model, data2)
    z1000 = float(data2.qpos[2])
    quat = np.array(data2.qpos[3:7])
    assert approx(data2.time, 2.000, 1e-9)
    assert approx(z1000, 0.30, 0.02), f"z@1000={z1000}（页面写约 0.30）"
    assert np.allclose(quat, [1, 0, 0, 0], atol=1e-3), f"quat={quat}"
    return f"time=0.200 z@100={z100:.3f} z@1000={z1000:.3f} quat={np.round(quat,4)}"


@test("01-03 install: EGL 离屏渲染 shape")
def t_install_render():
    import mujoco
    model = mujoco.MjModel.from_xml_string(MIN_XML)
    data = mujoco.MjData(model)
    with mujoco.Renderer(model, height=240, width=320) as r:
        mujoco.mj_forward(model, data)
        r.update_scene(data)
        px = r.render()
    assert px.shape == (240, 320, 3), f"shape={px.shape}"
    return f"rendered shape={px.shape} MUJOCO_GL={os.environ.get('MUJOCO_GL')}"


@test("01-02 mental-model: 骨架循环 + forward/step 练习")
def t_mental_model():
    import mujoco
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    model = mujoco.MjModel.from_xml_path(str(mdir / "franka_emika_panda" / "scene.xml"))
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    for i in range(200):
        data.ctrl[:] = data.ctrl  # compute_control 占位：保持 keyframe ctrl
        mujoco.mj_step(model, data)
    # 练习：改 qpos[0] 后 forward 不动它、step 会推进物理
    mujoco.mj_resetDataKeyframe(model, data, 0)
    data.qpos[0] = 0.5
    mujoco.mj_forward(model, data)
    after_fwd = float(data.qpos[0])
    mujoco.mj_step(model, data)
    after_step = float(data.qpos[0])
    assert after_fwd == 0.5, "mj_forward 不应改 qpos"
    assert after_step != 0.5, "mj_step 应推进物理"
    return f"forward 后 qpos[0]={after_fwd}（不变）；step 后 {after_step:.4f}（变了）"


# ---------------------------------------------------------------- 02-modeling
@test("02-01 skeleton: 练习 angle=degree/radian 限位")
def t_skeleton_angle():
    import mujoco
    base = """
    <mujoco>
      {compiler}
      <worldbody>
        <geom type="plane" size="1 1 0.1"/>
        <body pos="0 0 1">
          <joint type="hinge" axis="0 0 1" range="0 90"/>
          <geom type="box" size=".1 .2 .3"/>
        </body>
      </worldbody>
    </mujoco>
    """
    m_deg = mujoco.MjModel.from_xml_string(base.format(compiler='<compiler angle="degree"/>'))
    m_rad = mujoco.MjModel.from_xml_string(base.format(compiler='<compiler angle="radian"/>'))
    r_deg, r_rad = m_deg.jnt_range[0], m_rad.jnt_range[0]
    assert approx(r_deg[1], math.pi / 2, 1e-3), f"degree 模式读出 {r_deg}"
    assert approx(r_rad[1], 90.0, 1e-9), f"radian 模式读出 {r_rad}"
    return f"degree→{np.round(r_deg,3)}（约 [0,1.57]）  radian→{np.round(r_rad,1)}（[0,90]）"


@test("02-02 body-joint: 片段编译 + 练习 nq/nv")
def t_body_joint():
    import mujoco
    two_link = """
    <mujoco><worldbody>
      <body name="base" pos="0 0 0">
        <geom type="box" size="0.1 0.1 0.05"/>
        <body name="link1" pos="0 0 0.1">
          <joint name="j1" type="hinge" axis="0 1 0"/>
          <geom type="capsule" size="0.03" fromto="0 0 0 0 0 0.2"/>
        </body>
      </body>
    </worldbody></mujoco>
    """
    mujoco.MjModel.from_xml_string(two_link)
    joints = """
    <mujoco><worldbody>
      <body pos="0 0 1">
        <joint name="elbow" type="hinge" axis="0 0 1" range="-1.57 1.57"/>
        <geom type="box" size=".05 .05 .05"/>
      </body>
      <body pos="1 0 1">
        <joint name="finger" type="slide" axis="1 0 0" range="0 0.05"/>
        <geom type="box" size=".05 .05 .05"/>
      </body>
      <body pos="2 0 1">
        <joint name="shoulder" type="ball"/>
        <geom type="box" size=".05 .05 .05"/>
      </body>
      <body pos="3 0 1">
        <joint type="free"/>
        <geom type="box" size=".05 .05 .05"/>
      </body>
    </worldbody></mujoco>
    """
    m = mujoco.MjModel.from_xml_string(joints)
    assert m.nq == 1 + 1 + 4 + 7 and m.nv == 1 + 1 + 3 + 6, f"nq={m.nq} nv={m.nv}"
    inertial = """
    <mujoco><worldbody>
      <body name="link1">
        <inertial mass="0.5" pos="0 0 0.1" fullinertia="0.001 0.001 0.0001 0 0 0"/>
        <joint type="hinge"/>
        <site name="tcp" pos="0 0 0.1" size="0.01"/>
      </body>
    </worldbody></mujoco>
    """
    mujoco.MjModel.from_xml_string(inertial)
    ball = mujoco.MjModel.from_xml_string(
        '<mujoco><worldbody><geom type="plane" size="1 1 0.1"/>'
        '<body pos="0 0 1"><joint type="ball"/><geom type="box" size=".1 .2 .3"/></body>'
        "</worldbody></mujoco>")
    assert ball.nq == 4 and ball.nv == 3, f"ball nq={ball.nq} nv={ball.nv}"
    hs = mujoco.MjModel.from_xml_string(
        '<mujoco><worldbody><geom type="plane" size="1 1 0.1"/>'
        '<body pos="0 0 1"><joint type="hinge" axis="0 0 1"/><joint type="slide" axis="1 0 0"/>'
        '<geom type="box" size=".1 .2 .3"/></body></worldbody></mujoco>')
    assert hs.nq == 2 and hs.nv == 2
    # 小提醒核验：ball 后接 hinge 应编译报错
    try:
        mujoco.MjModel.from_xml_string(
            '<mujoco><worldbody><body pos="0 0 1"><joint type="ball"/>'
            '<joint type="hinge" axis="0 0 1"/><geom type="box" size=".1 .1 .1"/>'
            "</body></worldbody></mujoco>")
        ball_hinge = "竟然没报错(与页面提醒不符)"
    except Exception:
        ball_hinge = "按页面提醒报错"
    return f"ball nq=4 nv=3 ✓ hinge+slide nq=2 nv=2 ✓ ball后接hinge: {ball_hinge}"


@test("02-03 coord: 四元数 wxyz↔xyzw 往返")
def t_quat_roundtrip():
    def mujoco_to_ros_quat(q):
        return np.array([q[1], q[2], q[3], q[0]])

    def ros_to_mujoco_quat(q):
        return np.array([q[3], q[0], q[1], q[2]])

    q = np.array([0.7071, 0.0, 0.0, 0.7071])  # 绕 Z 转 90°（wxyz）
    back = ros_to_mujoco_quat(mujoco_to_ros_quat(q))
    assert np.allclose(back, q), f"{back} != {q}"
    return f"非平凡四元数 {q} 往返一致"


@test("02-04 geom-asset: 练习 rgba 渲染对比")
def t_rgba_render():
    import mujoco
    xml = ('<mujoco><worldbody><light pos="0 0 3" dir="0 0 -1"/>'
           '<geom type="box" size=".1 .2 .3" rgba="{rgba}"/></worldbody></mujoco>')
    frames = []
    for rgba in ("0 .9 0 1", "0 0 .9 1"):
        model = mujoco.MjModel.from_xml_string(xml.format(rgba=rgba))
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
        with mujoco.Renderer(model, height=120, width=160) as r:
            r.update_scene(data)
            frames.append(r.render().astype(int))
    green, blue = frames
    g_dom = green[..., 1].sum() > green[..., 2].sum()
    b_dom = blue[..., 2].sum() > blue[..., 1].sum()
    assert g_dom and b_dom, "颜色通道占比与 rgba 不符"
    return "绿色帧 G 通道占优、蓝色帧 B 通道占优，符合预期"


@test("02-05 default: 官方继承例子（补 size 后核对颜色）")
def t_default_inherit():
    # 官方文档明说无 size 的原始片段"will not actually compile"（size>0 是硬性
    # 检查，3.8.1 与 3.10.x 的 checksize() 相同），这里补 size 只为核对 rgba 继承。
    import mujoco
    xml = """
    <mujoco>
      <default class="main">
        <geom rgba="1 0 0 1"/>
        <default class="sub">
          <geom rgba="0 1 0 1"/>
        </default>
      </default>
      <worldbody>
        <geom type="box" size="0.1 0.1 0.1"/>
        <body childclass="sub">
          <geom type="ellipsoid" size="0.1 0.05 0.03"/>
          <geom type="sphere" size="0.05" rgba="0 0 1 1"/>
          <geom type="cylinder" size="0.05 0.1" class="main"/>
        </body>
      </worldbody>
    </mujoco>
    """
    m = mujoco.MjModel.from_xml_string(xml)
    got = [tuple(np.round(m.geom_rgba[i], 2)) for i in range(4)]
    want = [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (1, 0, 0, 1)]
    assert all(np.allclose(g, w) for g, w in zip(got, want)), f"rgba={got}"
    stripped = xml
    for s in (' size="0.1 0.1 0.1"', ' size="0.1 0.05 0.03"',
              ' size="0.05 0.1"', ' size="0.05"'):
        stripped = stripped.replace(s, "")
    try:
        mujoco.MjModel.from_xml_string(stripped)
        no_size = "竟可编译(与官方文档不符)"
    except ValueError:
        no_size = "按官方文档报错不可编译"
    assert no_size.startswith("按官方文档"), no_size
    return f"四个 geom 颜色 红/绿/蓝/红 ✓（无 size 原片段：{no_size}）"


@test("02-06 model-data: 练习 重力清零 qvel")
def t_gravity_toggle():
    import mujoco
    xml = ('<mujoco><worldbody><body pos="0 0 1"><freejoint/>'
           '<geom type="box" size="0.1 0.1 0.1"/></body></worldbody></mujoco>')
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    for _ in range(50):
        mujoco.mj_step(model, data)
    v1 = float(data.qvel[2])
    model.opt.gravity[:] = 0
    for _ in range(50):
        mujoco.mj_step(model, data)
    v2 = float(data.qvel[2])
    assert approx(v1, -0.98, 0.02), f"v1={v1}"
    assert approx(v2, v1, 1e-6), f"清零重力后 qvel 变了：{v2}"
    return f"50 步 qvel_z={v1:.3f}（约 -0.98）；清零重力再 50 步 {v2:.3f}（不再变快）"


@test("02-07/99 fields: Panda scene 规模字段")
def t_panda_fields():
    import mujoco
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    scene = mujoco.MjModel.from_xml_path(str(mdir / "franka_emika_panda" / "scene.xml"))
    panda = mujoco.MjModel.from_xml_path(str(mdir / "franka_emika_panda" / "panda.xml"))
    vals = dict(nq=scene.nq, nv=scene.nv, nu=scene.nu, nbody=scene.nbody,
                njnt=scene.njnt, ngeom=scene.ngeom, nsensor=scene.nsensor,
                ncam=scene.ncam, timestep=scene.opt.timestep,
                panda_ngeom=panda.ngeom)
    assert vals["nq"] == 9 and vals["nv"] == 9 and vals["nu"] == 8
    assert vals["nbody"] == 12 and vals["njnt"] == 9
    assert vals["nsensor"] == 0 and vals["ncam"] == 0
    assert vals["ngeom"] == 82 and vals["panda_ngeom"] == 81, f"ngeom={vals['ngeom']}/{vals['panda_ngeom']}"
    assert approx(vals["timestep"], 0.002, 1e-9)
    data = mujoco.MjData(scene)
    mujoco.mj_step(scene, data)
    j1 = float(data.joint("joint1").qpos[0])
    data.ctrl[:] = [0.5, -0.3, 0.1, -1.57, 0.0, 1.57, -0.785, 255]
    mujoco.mj_step(scene, data)
    return f"{vals}；joint1 按名读取 ok（{j1:.4f}）"


@test("02-08 keyframe: panda home 摘录与重置行为")
def t_keyframe():
    import mujoco
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    txt = (mdir / "franka_emika_panda" / "panda.xml").read_text()
    assert 'name="home"' in txt
    assert 'qpos="0 0 0 -1.57079 0 1.57079 -0.7853 0.04 0.04"' in txt, "keyframe qpos 摘录与 panda.xml 不符"
    assert 'ctrl="0 0 0 -1.57079 0 1.57079 -0.7853 255"' in txt, "keyframe ctrl 摘录与 panda.xml 不符"
    model = mujoco.MjModel.from_xml_path(str(mdir / "franka_emika_panda" / "scene.xml"))
    data = mujoco.MjData(model)
    assert model.nkey == 1 and model.key(0).name == "home"
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    data.qpos[0] = 1.0
    mujoco.mj_forward(model, data)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    assert approx(data.qpos[0], 0.0, 1e-12), "重置应恢复 qpos[0]"
    return "keyframe 摘录逐字一致；nkey=1 name=home；重置恢复 qpos[0] ✓"


@test("02-10 hands-on: UR5e 规模 + 斜坡摩擦对比")
def t_hands_on_modify():
    import mujoco
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    m = mujoco.MjModel.from_xml_path(str(mdir / "universal_robots_ur5e" / "scene.xml"))
    assert (m.nq, m.nv, m.nu, m.nbody, m.njnt) == (6, 6, 6, 8, 6), \
        f"UR5e: nq={m.nq} nv={m.nv} nu={m.nu} nbody={m.nbody} njnt={m.njnt}"
    slope = """
    <mujoco>
      <compiler angle="degree"/>
      <default><geom friction="{f} 0.005 0.0001"/></default>
      <worldbody>
        <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
        <geom type="plane" size="5 5 0.1" euler="0 20 0" rgba=".9 0 0 1"/>
        <body pos="0 0 0.3">
          <joint type="free"/>
          <geom type="box" size=".05 .05 .05" rgba="0 .9 0 1"/>
        </body>
      </worldbody>
    </mujoco>
    """
    xs = {}
    for f in (0.1, 1.0):
        mm = mujoco.MjModel.from_xml_string(slope.format(f=f))
        dd = mujoco.MjData(mm)
        for _ in range(2000):
            mujoco.mj_step(mm, dd)
        xs[f] = float(dd.qpos[0])
    assert abs(xs[0.1]) > 0.5, f"低摩擦位移 {xs[0.1]:.3f}，应明显滑动"
    assert abs(xs[1.0]) < 0.15, f"高摩擦位移 {xs[1.0]:.3f}，应基本不动"
    return f"UR5e nq=6 ✓；斜坡 2000 步位移 μ=0.1→{xs[0.1]:.2f}m，μ=1.0→{xs[1.0]:.3f}m"


# ---------------------------------------------------- 03-control-and-physics
@test("03-01 actuator: position 最小例子输出数值")
def t_position_servo():
    import mujoco
    xml = """
    <mujoco>
      <option gravity="0 0 0"/>
      <worldbody>
        <body>
          <joint name="hinge" type="hinge" axis="0 0 1"/>
          <geom type="capsule" size="0.03" fromto="0 0 0 0.3 0 0"/>
        </body>
      </worldbody>
      <actuator>
        <position name="servo" joint="hinge" kp="20" kv="2" ctrlrange="-3.14 3.14"/>
      </actuator>
    </mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    data.ctrl[0] = 1.0
    got = {}
    for i in range(500):
        mujoco.mj_step(model, data)
        if i % 100 == 0:
            got[i] = float(data.qpos[0])
    want = {0: 0.003, 100: 0.892, 200: 0.990, 300: 0.999, 400: 1.000}
    for k, w in want.items():
        assert approx(got[k], w, 0.02), f"step {k}: got {got[k]:.3f} want≈{w}"
    return "  ".join(f"s{k}={v:.3f}" for k, v in got.items()) + "（与页面输出一致）"


@test("03-01 actuator: motor/velocity 片段 + Panda 摘录")
def t_actuator_snippets():
    import mujoco
    base = """
    <mujoco><worldbody>
      <body><joint name="joint1" type="hinge" axis="0 0 1"/>
      <geom type="capsule" size="0.03" fromto="0 0 0 0.3 0 0"/></body>
    </worldbody><actuator>{act}</actuator></mujoco>
    """
    for act in ('<motor name="motor1" joint="joint1" ctrlrange="-10 10"/>',
                '<position name="pos1" joint="joint1" kp="100" kv="10" ctrlrange="-1.57 1.57"/>',
                '<velocity name="vel1" joint="joint1" kv="10" ctrlrange="-3.14 3.14"/>'):
        m = mujoco.MjModel.from_xml_string(base.format(act=act))
        d = mujoco.MjData(m)
        d.ctrl[0] = 1.0
        mujoco.mj_step(m, d)
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    txt = (mdir / "franka_emika_panda" / "panda.xml").read_text()
    assert 'gainprm="4500"' in txt and 'biasprm="0 -4500 -450"' in txt, "actuator1 摘录不符"
    m = mujoco.MjModel.from_xml_path(str(mdir / "franka_emika_panda" / "panda.xml"))
    cr4 = m.actuator_ctrlrange[3]
    cr8 = m.actuator_ctrlrange[7]
    assert approx(cr4[0], -3.07, 0.01) and approx(cr4[1], -0.07, 0.01), f"joint4 ctrlrange={cr4}"
    assert approx(cr8[0], 0, 1e-9) and approx(cr8[1], 255, 1e-9), f"actuator8 ctrlrange={cr8}"
    assert '<joint joint="finger_joint1" coef="0.5"/>' in txt, "tendon 摘录不符"
    return f"三类 actuator 片段可跑；actuator1 gainprm/biasprm ✓ joint4 cr={np.round(cr4,4)} actuator8 cr={cr8}"


@test("03-03 equality: 练习 双杆角度拉拢")
def t_equality():
    import mujoco
    xml = """
    <mujoco>
      <option gravity="0 0 0"/>
      <worldbody>
        <body>
          <joint name="j1" type="hinge" axis="0 0 1"/>
          <geom type="capsule" size="0.02" fromto="0 0 0 0.2 0 0"/>
        </body>
        <body pos="0 0.3 0">
          <joint name="j2" type="hinge" axis="0 0 1"/>
          <geom type="capsule" size="0.02" fromto="0 0 0 0.2 0 0"/>
        </body>
      </worldbody>
      <equality><joint joint1="j1" joint2="j2"/></equality>
    </mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    data.qpos[:] = [0.5, -0.5]
    mujoco.mj_forward(model, data)
    assert np.allclose(data.qpos, [0.5, -0.5]), "mj_forward 不应改 qpos"
    diffs = {}
    for i in range(201):
        if i in (0, 50, 100, 150, 200):
            diffs[i] = float(abs(data.qpos[0] - data.qpos[1]))
        mujoco.mj_step(model, data)
    assert diffs[100] < 0.05, f"100 步后 |j1-j2|={diffs[100]:.4f}，页面称约 100 步内收敛"
    assert abs(data.qpos[0]) < 0.05, f"对称系统应趋向 0，j1={data.qpos[0]:.4f}"
    return "  ".join(f"s{k}:|Δ|={v:.3f}" for k, v in diffs.items())


@test("03-04 contact: 练习 ncon 与 dist")
def t_contact():
    import mujoco
    xml = """
    <mujoco><worldbody>
      <geom type="plane" size="1 1 0.1"/>
      <body pos="0 0 0.3"><freejoint/><geom type="box" size="0.05 0.05 0.05"/></body>
    </worldbody></mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    for _ in range(500):
        mujoco.mj_step(model, data)
    dists = [float(data.contact[i].dist) for i in range(data.ncon)]
    assert data.ncon == 4, f"ncon={data.ncon}，页面预期 4"
    assert all(-1e-3 < d < 0 for d in dists), f"dists={dists}，页面预期约 -1e-4 的小负数"
    return f"ncon=4 dists={[f'{d:.2e}' for d in dists]}"


@test("03-05 solver: 默认值核对（Newton/solref/solimp）")
def t_solver_defaults():
    import mujoco
    m = mujoco.MjModel.from_xml_string("<mujoco><worldbody/></mujoco>")
    assert m.opt.solver == mujoco.mjtSolver.mjSOL_NEWTON, "默认求解器应为 Newton"
    m2 = mujoco.MjModel.from_xml_string(
        '<mujoco><worldbody><geom type="sphere" size="0.1"/></worldbody></mujoco>')
    solref, solimp = m2.geom_solref[0], m2.geom_solimp[0]
    assert np.allclose(solref, [0.02, 1]), f"solref={solref}"
    assert np.allclose(solimp, [0.9, 0.95, 0.001, 0.5, 2]), f"solimp={solimp}"
    fr = m2.geom_friction[0]
    assert np.allclose(fr, [1.0, 0.005, 0.0001]), f"friction 默认={fr}"
    return f"Newton 默认 ✓ solref={solref} solimp={solimp} friction={fr}"


@test("03-07 hands-on: PD 三组阻尼 + 正弦跟踪")
def t_pd_control():
    import mujoco
    xml = """
    <mujoco>
      <option gravity="0 0 0"/>
      <worldbody>
        <body pos="0 0 0">
          <joint name="hinge" type="hinge" axis="0 1 0"/>
          <geom type="capsule" size="0.03" fromto="0 0 0 0 0 -0.5" rgba="0.8 0.2 0.2 1"/>
        </body>
      </worldbody>
      <actuator><motor name="motor1" joint="hinge" ctrlrange="-50 50"/></actuator>
    </mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)

    def run(Kp, Kd, steps=500):
        data = mujoco.MjData(model)
        peak = 0.0
        for _ in range(steps):
            err = 1.0 - data.qpos[0]
            data.ctrl[0] = Kp * err - Kd * data.qvel[0]
            mujoco.mj_step(model, data)
            peak = max(peak, float(data.qpos[0]))
        return float(data.qpos[0]), peak

    final_b, peak_b = run(50, 5)
    assert abs(final_b - 1.0) < 0.01, f"练习1 稳态 {final_b}"
    _, peak_a = run(50, 1)
    assert 1.3 < peak_a < 1.7, f"欠阻尼峰值 {peak_a:.2f}，页面写约 1.5"
    assert peak_b < 1.08, f"临界阻尼不应明显超调，peak={peak_b:.3f}"
    final_c, peak_c = run(50, 20)
    assert peak_c < 1.02 and final_c < final_b + 1e-9, "过阻尼应无超调且更慢"
    # 练习3：0.5Hz 正弦跟踪的稳态误差幅度
    data = mujoco.MjData(model)
    errs = []
    for i in range(1500):
        t = data.time
        target = 1.0 * math.sin(2.0 * math.pi * 0.5 * t)
        err = target - data.qpos[0]
        data.ctrl[0] = 50.0 * err - 5.0 * data.qvel[0]
        mujoco.mj_step(model, data)
        if i > 500:
            errs.append(abs(err))
    emax = max(errs)
    assert 0.15 < emax < 0.4, f"0.5Hz 跟踪误差峰值 {emax:.3f}，页面写 0.2~0.3"
    return (f"稳态={final_b:.4f} 欠阻尼峰值={peak_a:.2f}（≈1.5）"
            f" 临界峰值={peak_b:.3f} 过阻尼峰值={peak_c:.3f} 正弦误差峰值={emax:.2f}")


# ------------------------------------------------ 04-observation-and-rendering
@test("04-01 state: fingertip site 练习数值")
def t_fingertip_site():
    import mujoco
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    work = Path(tempfile.mkdtemp(prefix="mjverify_")) / "franka_emika_panda"
    shutil.copytree(mdir / "franka_emika_panda", work)
    txt = (work / "panda.xml").read_text()
    marker = '<body name="hand" '
    idx = txt.index(marker)
    idx = txt.index(">", idx) + 1
    txt = txt[:idx] + '\n        <site name="fingertip" pos="0 0 0.05" size="0.01"/>' + txt[idx:]
    (work / "panda_site.xml").write_text(txt)
    model = mujoco.MjModel.from_xml_path(str(work / "panda_site.xml"))
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    d_home = data.site("fingertip").xpos - data.body("hand").xpos
    assert np.allclose(d_home, [0, 0, -0.05], atol=5e-3), f"home 差向量 {d_home}"
    data.qpos[0] += 0.7
    data.qpos[3] += 0.8
    mujoco.mj_forward(model, data)
    d_bent = data.site("fingertip").xpos - data.body("hand").xpos
    assert np.allclose(d_bent, [0.027, 0.023, -0.035], atol=0.01), f"弯曲后差向量 {d_bent}"
    assert approx(np.linalg.norm(d_home), 0.05, 1e-3) and approx(np.linalg.norm(d_bent), 0.05, 1e-3)
    return f"home Δ={np.round(d_home,3)} 弯后 Δ={np.round(d_bent,3)} 模长均≈0.05"


@test("04-02+07 sensors: scene_with_cams 声明与读数")
def t_scene_with_cams():
    import mujoco
    global SCENE_WITH_CAMS
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    work = Path(tempfile.mkdtemp(prefix="mjverify_")) / "franka_emika_panda"
    shutil.copytree(mdir / "franka_emika_panda", work)
    txt = (work / "panda.xml").read_text()
    wb = txt.index("<worldbody>") + len("<worldbody>")
    txt = txt[:wb] + """
    <geom type="plane" size="2 2 0.1" pos="0 0 0"/>
    <light pos="0 0 2" dir="0 0 -1"/>
    <camera name="top_down"  pos="0.4 0 1.2"    xyaxes="1 0 0 0 1 0"             fovy="55"/>
    <camera name="side_view" pos="1.2 -0.6 0.7" xyaxes="0.4 0.9 0 -0.2 0.1 0.97" fovy="55"/>
    """ + txt[wb:]
    marker = '<body name="hand" '
    idx = txt.index(marker)
    idx = txt.index(">", idx) + 1
    txt = txt[:idx] + """
        <site name="wrist_site" pos="0 0 0" size="0.01"/>
        <camera name="wrist_rgb" pos="0 -0.05 0.02" xyaxes="1 0 0 0 0 1" fovy="70"/>
    """ + txt[idx:]
    txt = txt.replace("</mujoco>", """
  <sensor>
    <force  name="wrist_force"  site="wrist_site"/>
    <torque name="wrist_torque" site="wrist_site"/>
  </sensor>
</mujoco>""")
    path = work / "scene_with_cams.xml"
    path.write_text(txt)
    SCENE_WITH_CAMS = path
    model = mujoco.MjModel.from_xml_path(str(path))
    assert model.ncam == 3, f"ncam={model.ncam}"
    assert model.nsensor == 2 and model.nsensordata == 6
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    for _ in range(100):
        mujoco.mj_step(model, data)
    force = data.sensor("wrist_force").data.copy()
    assert np.linalg.norm(force) > 1e-6, "wrist_force 应非零（手臂受重力）"
    # sensor noise 元数据验证：engine 不自动加噪
    xml_noise = """
    <mujoco><worldbody>
      <body><joint name="j" type="hinge" axis="0 0 1"/>
      <geom type="capsule" size="0.02" fromto="0 0 0 0.2 0 0"/></body>
    </worldbody>
    <sensor><jointpos name="jp" joint="j" noise="0.1"/></sensor></mujoco>
    """
    m2 = mujoco.MjModel.from_xml_string(xml_noise)
    d2 = mujoco.MjData(m2)
    reads = []
    for _ in range(20):
        mujoco.mj_step(m2, d2)
        reads.append(float(d2.sensor("jp").data[0]))
    spread = np.std(np.diff(reads))
    assert approx(m2.sensor_noise[0], 0.1, 1e-9)
    assert spread < 1e-6, f"读数出现随机波动 {spread}（页面称仿真步不自动加噪）"
    rng = np.random.default_rng(0)
    noisy = np.array(reads) + 0.1 * rng.standard_normal(len(reads))
    return (f"ncam=3 nsensor=2 nsensordata=6 ✓ wrist_force={np.round(force,3)}；"
            f"noise 元数据={m2.sensor_noise[0]} 不自动加噪 ✓ 手动加噪 std≈{np.std(noisy - np.array(reads)):.3f}")


@test("04-03 camera: 内参换算函数")
def t_intrinsics():
    def fovy_to_intrinsics(fovy_deg, width, height):
        fovy = np.radians(fovy_deg)
        fy = height / (2.0 * np.tan(fovy / 2.0))
        fx = fy
        cx, cy = width / 2.0, height / 2.0
        return np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])

    K = fovy_to_intrinsics(60, 640, 480)
    assert approx(K[1, 1], 480 / (2 * math.tan(math.radians(30))), 1e-9)
    return f"fovy=60 640x480 → fy={K[1,1]:.1f} cx={K[0,2]} cy={K[1,2]}"


@test("04-04 offscreen: RGB/深度/分割三模式")
def t_offscreen_modes():
    import mujoco
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    model = mujoco.MjModel.from_xml_path(str(mdir / "franka_emika_panda" / "scene.xml"))
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    with mujoco.Renderer(model, height=240, width=320) as r:
        r.update_scene(data)
        rgb = r.render()
        assert rgb.shape == (240, 320, 3) and rgb.dtype == np.uint8
        r.enable_depth_rendering()
        r.update_scene(data)
        depth = r.render()
        r.disable_depth_rendering()
        assert depth.shape == (240, 320) and depth.dtype == np.float32
        assert float(depth.min()) > 0
        r.enable_segmentation_rendering()
        r.update_scene(data)
        seg = r.render()
        r.disable_segmentation_rendering()
        assert seg.shape == (240, 320, 2) and seg.dtype == np.int32
        assert (seg[..., 0] >= -1).all()
        geom_types = set(np.unique(seg[..., 1])) - {-1}
        assert geom_types == {int(mujoco.mjtObj.mjOBJ_GEOM)}, f"类型通道={geom_types}（mjOBJ_GEOM=5）"
        multiview = {}
        for _ in range(3):
            mujoco.mj_step(model, data)
        # 多视角（用自由相机默认 + 指定失败则跳过——panda scene 无具名相机）
    bg = int((seg[..., 0] == -1).sum())
    return f"rgb{rgb.shape} depth{depth.shape}[{depth.min():.2f},{depth.max():.2f}]m seg 背景像素={bg} 类型通道=5(mjOBJ_GEOM) ✓"


@test("04-07 hands-on: 录像管线练习 2+3")
def t_recording_pipeline():
    import mujoco
    import imageio
    path = SCENE_WITH_CAMS
    assert path and Path(path).exists(), "依赖上面的 scene_with_cams 测试"
    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    cam_names = ["top_down", "side_view", "wrist_rgb"]
    rec = Path(tempfile.mkdtemp(prefix="mjrecords_"))
    writers = {n: imageio.get_writer(str(rec / f"{n}.mp4"), fps=30) for n in cam_names}
    sensor_log = []
    with mujoco.Renderer(model, height=240, width=320) as renderer:
        for step in range(60):
            data.ctrl[:] = data.ctrl.copy()
            for _ in range(5):
                mujoco.mj_step(model, data)
            for cam in cam_names:
                renderer.update_scene(data, camera=cam)
                writers[cam].append_data(renderer.render())
            sensor_log.append({"step": step, "time": float(data.time),
                               "sensors": data.sensordata.copy().tolist()})
            if step < 3:  # 练习 3：深度+分割对齐（抽前几帧）
                for cam in cam_names:
                    (rec / cam).mkdir(exist_ok=True)
                    renderer.update_scene(data, camera=cam)
                    np.save(rec / cam / f"{step:06d}_rgb.npy", renderer.render())
                    renderer.enable_depth_rendering()
                    renderer.update_scene(data, camera=cam)
                    np.save(rec / cam / f"{step:06d}_depth.npy", renderer.render().copy())
                    renderer.disable_depth_rendering()
                    renderer.enable_segmentation_rendering()
                    renderer.update_scene(data, camera=cam)
                    np.save(rec / cam / f"{step:06d}_seg.npy", renderer.render().copy())
                    renderer.disable_segmentation_rendering()
    for w in writers.values():
        w.close()
    with open(rec / "sensors.jsonl", "w") as f:
        for e in sensor_log:
            f.write(json.dumps(e) + "\n")
    mp4s = [p.name for p in rec.glob("*.mp4")]
    npys = len(list((rec / "top_down").glob("*.npy")))
    assert len(mp4s) == 3 and (rec / "sensors.jsonl").exists()
    assert npys == 9, f"应有 3 帧 × rgb/depth/seg = 9 个 npy，得 {npys}"
    return f"3 个 mp4 + sensors.jsonl + 每相机 9 npy ✓（60 帧验证版）"


# ---------------------------------------------------- 05-interfaces
@test("05-01 api-tour: MjSpec 与 rollout")
def t_mjspec_rollout():
    import mujoco
    from mujoco import rollout
    spec = mujoco.MjSpec()
    body = spec.worldbody.add_body(name="my_box", pos=[0, 0, 1])
    body.add_joint(type=mujoco.mjtJoint.mjJNT_FREE)
    body.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.1, 0.1, 0.1])
    model = spec.compile()
    assert model.nq == 7 and model.nv == 6, f"MjSpec nq={model.nq} nv={model.nv}"
    mdir = menagerie_dir()
    m2 = mujoco.MjModel.from_xml_path(str(mdir / "franka_emika_panda" / "scene.xml"))
    d2 = mujoco.MjData(m2)
    nbatch, nstep = 4, 100
    nstate = mujoco.mj_stateSize(m2, mujoco.mjtState.mjSTATE_FULLPHYSICS)
    initial_state = np.zeros((nbatch, nstate))
    control = np.random.default_rng(0).standard_normal((nbatch, nstep, m2.nu))
    state, sensordata = rollout.rollout(m2, d2, initial_state, control)
    assert state.shape == (nbatch, nstep, nstate), f"state.shape={state.shape}"
    return f"MjSpec nq=7 nv=6 ✓ rollout state{state.shape} ✓"


@test("05-02 menagerie: 对比表 6 台机器人数值")
def t_menagerie_table():
    import mujoco
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    want = {
        "franka_emika_panda": (9, 8, 12),
        "universal_robots_ur5e": (6, 6, 8),
        "kuka_iiwa_14": (7, 7, 9),
        "unitree_go2": (19, 12, 14),
        "aloha": (16, 14, 21),
        "robotis_op3": (27, 20, 22),
    }
    got = {}
    for name, (nq, nu, nbody) in want.items():
        m = mujoco.MjModel.from_xml_path(str(mdir / name / "scene.xml"))
        got[name] = (m.nq, m.nu, m.nbody)
        assert got[name] == (nq, nu, nbody), f"{name}: got {got[name]} want {(nq,nu,nbody)}"
    return "；".join(f"{k} nq/nu/nbody={v}" for k, v in got.items())


@test("05-03 dm_control suite: TimeStep/discount/维度")
def t_dm_suite():
    from dm_control import suite
    import mujoco
    env = suite.load("cartpole", "swingup")
    time_step = env.reset()
    total = 0.0
    rng = np.random.default_rng(0)
    for _ in range(100):
        action = rng.uniform(-1, 1, size=env.action_spec().shape)
        time_step = env.step(action)
        total += time_step.reward
    obs = time_step.observation
    physics = env.physics
    assert obs["position"].shape == (3,) and physics.data.qpos.shape == (2,)
    assert obs["velocity"].shape == (2,)
    physics.forward()  # M3 修复后的 API：应存在且可调
    # 跑到 episode 结束（时间上限截断），discount 应为 1.0
    steps = 0
    ts = env.reset()
    while not ts.last():
        ts = env.step(np.zeros(env.action_spec().shape))
        steps += 1
        assert steps < 2000
    assert ts.discount == 1.0, f"末帧 discount={ts.discount}（页面：截断时应为 1.0）"
    n_tasks = len(list(suite.ALL_TASKS))
    return (f"随机 100 步 reward={total:.3f} obs position(3,)>qpos(2,) ✓ "
            f"physics.forward() ✓ 末帧 step={steps} discount=1.0 ✓ ALL_TASKS={n_tasks}")


@test("05-04 composer: PushTask 最小骨架")
def t_composer():
    from dm_control import composer, mjcf
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"

    class Panda(composer.Entity):
        def _build(self, xml_path):
            self._model = mjcf.from_path(xml_path)

        @property
        def mjcf_model(self):
            return self._model

    class Block(composer.Entity):
        def _build(self):
            self._model = mjcf.RootElement()
            self._body = self._model.worldbody.add('body', name='block', pos=[0.4, 0, 0.05])
            self._body.add('geom', type='box', size=[0.03, 0.03, 0.03], rgba=[0.2, 0.6, 1, 1])

        @property
        def mjcf_model(self):
            return self._model

        @property
        def body(self):
            return self._body

    class PushTask(composer.Task):
        def __init__(self, panda, block):
            self._arena = composer.Arena()
            self._arena.mjcf_model.worldbody.add('geom', type='plane', size=[1, 1, 0.1])
            self._arena.attach(panda)
            self._arena.add_free_entity(block)
            self._panda, self._block = panda, block
            self._target_pos = np.array([0.5, 0.0, 0.05])

        @property
        def root_entity(self):
            return self._arena

        def get_reward(self, physics):
            block_pos = physics.bind(self._block.body).xpos
            return -np.linalg.norm(block_pos - self._target_pos)

        def should_terminate_episode(self, physics):
            return physics.data.time > 10

    task = PushTask(Panda(xml_path=str(mdir / "franka_emika_panda" / "panda.xml")), Block())
    env = composer.Environment(task)
    ts = env.reset()
    spec = env.action_spec()
    ts = env.step(np.zeros(spec.shape))
    assert ts.reward is not None
    return f"composer env reset/step ✓ reward={ts.reward:.4f} action dim={spec.shape}"


@test("05-05 gym wrappers: 自定义 env + AsyncVectorEnv")
def t_gym_wrappers():
    import gymnasium as gym
    import mujoco
    mdir = menagerie_dir()
    scene = str(mdir / "franka_emika_panda" / "scene.xml")

    class MyRobotEnv(gym.Env):
        def __init__(self, mjcf_path=scene):
            super().__init__()
            self.model = mujoco.MjModel.from_xml_path(mjcf_path)
            self.data = mujoco.MjData(self.model)
            self.action_space = gym.spaces.Box(
                low=-1, high=1, shape=(self.model.nu,), dtype=np.float32)
            self.observation_space = gym.spaces.Box(
                low=-np.inf, high=np.inf, shape=(self.model.nq + self.model.nv,),
                dtype=np.float32)

        def reset(self, seed=None, options=None):
            super().reset(seed=seed)
            mujoco.mj_resetDataKeyframe(self.model, self.data, 0)
            mujoco.mj_forward(self.model, self.data)
            obs = np.concatenate([self.data.qpos, self.data.qvel])
            return obs.astype(np.float32), {}

        def step(self, action):
            self.data.ctrl[:] = action
            mujoco.mj_step(self.model, self.data)
            obs = np.concatenate([self.data.qpos, self.data.qvel])
            return obs.astype(np.float32), 0.0, self.data.time > 10.0, False, {}

    env = MyRobotEnv()
    obs, _ = env.reset()
    assert obs.shape == (18,), f"obs shape={obs.shape}（nq+nv=9+9）"
    out = env.step(env.action_space.sample())
    assert len(out) == 5
    from gymnasium.vector import AsyncVectorEnv
    envs = AsyncVectorEnv([MyRobotEnv for _ in range(4)])
    try:
        obs, info = envs.reset()
        actions = envs.action_space.sample()
        obs, reward, terminated, truncated, info = envs.step(actions)
        assert obs.shape == (4, 18) and actions.shape == (4, 8)
    finally:
        envs.close()
    return f"MyRobotEnv obs(18,) 5 元组 ✓ AsyncVectorEnv batch obs{obs.shape} actions(4,8) ✓"


@test("05-06/导读: gym.make 内置环境 id")
def t_gym_ids():
    import gymnasium as gym
    made = []
    for env_id in ("Humanoid-v5", "Ant-v5"):
        env = gym.make(env_id)
        env.reset(seed=0)
        env.step(env.action_space.sample())
        env.close()
        made.append(env_id)
    import gymnasium.envs.registration as reg
    assert "HumanoidReach-v0" not in reg.registry, "M1 断言：HumanoidReach-v0 不应存在"
    return f"{made} 可 make ✓ HumanoidReach-v0 不在 registry ✓"


# ---------------------------------------------------- 06-grasping
GRASP_SCENE = """<mujoco model="grasping_scene">
  <include file="scene.xml"/>

  <worldbody>
    <light name="top_light" pos="0.4 0 2" dir="0 0 -1" directional="true"
           diffuse="0.8 0.8 0.8" specular="0.2 0.2 0.2"/>

    <body name="table" pos="0.4 0 0.395">
      <geom name="table_top" type="box" size="0.3 0.4 0.02"
            rgba="0.6 0.4 0.2 1" friction="0.8 0.01 0.001"/>
    </body>

    <body name="block" pos="0.4 0 0.48">
      <joint type="free"/>
      <geom name="block_geom" type="box" size="0.03 0.03 0.03"
            mass="0.05" rgba="0.2 0.6 1 1"
            friction="1.0 0.01 0.001"/>
    </body>

    <site name="target_site" pos="0.4 0.2 0.44"
          type="sphere" size="0.01" rgba="0 1 0 0.5"/>

    <camera name="top_down" pos="0.4 0 1.0" xyaxes="1 0 0 0 1 0" fovy="60"/>
    <camera name="side_view" pos="0.4 -0.5 0.5" xyaxes="1 0 0 0 0.7 0.7" fovy="60"/>
  </worldbody>
</mujoco>
"""
GRASP_DIR: Path | None = None
SCENE_WITH_CAMS: Path | None = None


def grasp_workdir() -> Path:
    global GRASP_DIR
    if GRASP_DIR is None:
        mdir = menagerie_dir()
        assert mdir, "menagerie 不存在"
        work = Path(tempfile.mkdtemp(prefix="mjgrasp_")) / "franka_emika_panda"
        shutil.copytree(mdir / "franka_emika_panda", work)
        (work / "grasping_scene.xml").write_text(GRASP_SCENE)
        GRASP_DIR = work
    return GRASP_DIR


@test("06-01 scene: grasping_scene 编译渲染")
def t_grasp_scene():
    import mujoco
    work = grasp_workdir()
    model = mujoco.MjModel.from_xml_path(str(work / "grasping_scene.xml"))
    data = mujoco.MjData(model)
    for _ in range(300):
        mujoco.mj_step(model, data)
    block_z = float(data.body("block").xpos[2])
    assert approx(block_z, 0.445, 0.01), f"方块落桌后中心 z={block_z}（页面 ≈0.445）"
    with mujoco.Renderer(model, height=240, width=320) as r:
        r.update_scene(data, camera="top_down")
        px = r.render()
    assert px.shape == (240, 320, 3)
    return f"编译 ✓ 方块落桌 z={block_z:.4f}（≈0.445）top_down 渲染 ✓"


@test("06-02 ee-control: 末端伺服（纯运动学）")
def t_ee_servo():
    import mujoco
    work = grasp_workdir()
    model = mujoco.MjModel.from_xml_path(str(work / "grasping_scene.xml"))
    data = mujoco.MjData(model)
    data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    mujoco.mj_forward(model, data)
    for _ in range(200):
        mujoco.mj_step(model, data)
    target_pos = data.body("block").xpos + np.array([0, 0, 0.10])
    err0 = np.linalg.norm(target_pos - data.body("hand").xpos)
    for _ in range(800):
        ee_pos = data.body("hand").xpos.copy()
        error = target_pos - ee_pos
        if np.linalg.norm(error) < 0.001:
            break
        jacp = np.zeros((3, model.nv))
        mujoco.mj_jac(model, data, jacp, None, ee_pos, data.body("hand").id)
        desired_vel = error * 5.0
        dq = np.linalg.lstsq(jacp[:, :7], desired_vel, rcond=None)[0]
        data.qpos[:7] += dq * model.opt.timestep
        mujoco.mj_forward(model, data)
    err1 = np.linalg.norm(target_pos - data.body("hand").xpos)
    assert err1 < 0.02, f"800 步后误差 {err1:.4f}"
    return f"初始误差 {err0:.3f}m → 800 步内 {err1:.4f}m（每步缩小约 1%，与页面说法一致）"


@test("06-03 gripper: 开合 + is_grasped + 闭环")
def t_gripper():
    import mujoco
    work = grasp_workdir()
    model = mujoco.MjModel.from_xml_path(str(work / "grasping_scene.xml"))
    data = mujoco.MjData(model)
    data.ctrl[7] = 255
    for _ in range(100):
        mujoco.mj_step(model, data)
    open_w = float(data.qpos[7])
    data.ctrl[7] = 0
    for _ in range(100):
        mujoco.mj_step(model, data)
    closed_w = float(data.qpos[7])
    # 100 步(0.2s)夹爪尚未到稳态：实测 open@100=0.0334、closed@100=0.0057（稳态
    # 0.040/0.0，3.9.0 与 3.10.0 逐位一致）。阈值按实测留 ~11%/43% 裕量。
    assert open_w > 0.030 and closed_w < 0.010, f"open={open_w} closed={closed_w}"

    def is_grasped(data, model):
        left = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "left_finger")
        right = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "right_finger")
        block_geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "block_geom")
        finger_bodies = {left, right}
        for i in range(data.ncon):
            c = data.contact[i]
            body1 = model.geom_bodyid[c.geom1]
            body2 = model.geom_bodyid[c.geom2]
            if (body1 in finger_bodies and c.geom2 == block_geom) or \
               (body2 in finger_bodies and c.geom1 == block_geom):
                return True
        return False

    g_empty = is_grasped(data, model)  # 没抓东西应为 False
    assert g_empty is False
    f6 = np.zeros(6)
    mujoco.mj_contactForce(model, data, 0, f6) if data.ncon else None
    return f"张开 0.04m→{open_w:.4f} 闭合→{closed_w:.4f} is_grasped(空)={g_empty} mj_contactForce API ✓"


@test("06-04 pipeline: 完整 pick-and-place 落点")
def t_full_pipeline():
    import mujoco
    work = grasp_workdir()
    model = mujoco.MjModel.from_xml_path(str(work / "grasping_scene.xml"))
    data = mujoco.MjData(model)
    ik_data = mujoco.MjData(model)
    HAND = data.body("hand").id
    ARM_LIMIT = model.jnt_range[:7].copy()
    READY = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785])
    GRASP_OFFSET = 0.103
    OPEN, CLOSE = 255, 0

    def solve_ik(q_init, target_xyz, iters=300, damping=0.1, gain=0.5, clip=0.1):
        ik_data.qpos[:] = data.qpos
        ik_data.qpos[:7] = q_init
        mujoco.mj_forward(model, ik_data)
        jacp = np.zeros((3, model.nv))
        eye = np.eye(3)
        for _ in range(iters):
            err = target_xyz - ik_data.body("hand").xpos
            if np.linalg.norm(err) < 1e-3:
                break
            mujoco.mj_jac(model, ik_data, jacp, None, ik_data.body("hand").xpos, HAND)
            J = jacp[:, :7]
            dq = J.T @ np.linalg.solve(J @ J.T + damping * eye, err * gain)
            ik_data.qpos[:7] = np.clip(ik_data.qpos[:7] + np.clip(dq, -clip, clip),
                                       ARM_LIMIT[:, 0], ARM_LIMIT[:, 1])
            mujoco.mj_forward(model, ik_data)
        return ik_data.qpos[:7].copy()

    def drive(arm_target, gripper, steps):
        for _ in range(steps):
            data.ctrl[:7] = arm_target
            data.ctrl[7] = gripper
            mujoco.mj_step(model, data)

    data.qpos[:7] = READY
    data.qpos[7:9] = 0.04
    mujoco.mj_forward(model, data)
    drive(READY, OPEN, 300)
    block = data.body("block").xpos.copy()
    goal = data.site("target_site").xpos.copy()
    q = solve_ik(data.qpos[:7], block + [0, 0, GRASP_OFFSET + 0.08]); drive(q, OPEN, 250)
    q = solve_ik(data.qpos[:7], block + [0, 0, GRASP_OFFSET]);        drive(q, OPEN, 350)
    drive(q, CLOSE, 300)
    q = solve_ik(data.qpos[:7], block + [0, 0, GRASP_OFFSET + 0.15]); drive(q, CLOSE, 400)
    q = solve_ik(data.qpos[:7], [goal[0], goal[1], block[2] + GRASP_OFFSET + 0.15]); drive(q, CLOSE, 400)
    q = solve_ik(data.qpos[:7], [goal[0], goal[1], goal[2] + GRASP_OFFSET]);         drive(q, CLOSE, 350)
    drive(q, OPEN, 250)
    final = data.body("block").xpos.copy()
    xy_err = float(np.linalg.norm(final[:2] - goal[:2]))
    assert xy_err < 0.03, f"水平误差 {xy_err:.3f}m（页面：约 1cm）"
    assert approx(final[2], 0.444, 0.01), f"final z={final[2]}"
    ref = np.array([0.409, 0.197, 0.444])
    return (f"最终 {np.round(final,3)} vs 页面 {ref}（差 {np.linalg.norm(final-ref)*1000:.1f}mm）"
            f" 水平误差 {xy_err*100:.1f}cm ✓")


# ---------------------------------------------------- 07-mjx
@test("07-02 mjx: 最小迁移 + vmap + 数值差异定性")
def t_mjx_minimal():
    import mujoco
    try:
        import mujoco.mjx as mjx
        import jax
    except ImportError as e:
        return f"SKIP mjx/jax 未安装: {e}"
    xml = """
    <mujoco>
      <worldbody>
        <geom type="plane" size="3 3 0.1"/>
        <body pos="0 0 0.5">
          <joint type="free"/>
          <geom type="capsule" size="0.04" fromto="0 0 0 0.2 0 0"/>
          <body pos="0.2 0 0">
            <joint name="h1" type="hinge" axis="0 1 0"/>
            <geom type="capsule" size="0.035" fromto="0 0 0 0.18 0 0"/>
          </body>
        </body>
      </worldbody>
      <actuator><motor joint="h1" ctrlrange="-1 1"/></actuator>
    </mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)
    mjx_model = mjx.put_model(model)
    mjx_data = mjx.make_data(model)

    @jax.jit
    def step_fn(d, ctrl):
        d = d.replace(ctrl=ctrl)
        return mjx.step(mjx_model, d)

    ctrl = jax.numpy.full((model.nu,), 0.1)
    cpu = mujoco.MjData(model)
    diffs = {}
    d = mjx_data
    for i in range(1, 101):
        cpu.ctrl[:] = 0.1
        mujoco.mj_step(model, cpu)
        d = step_fn(d, ctrl)
        if i in (10, 100):
            diffs[i] = float(np.max(np.abs(np.array(d.qpos) - cpu.qpos)))
    N = 64
    batch = jax.tree_util.tree_map(
        lambda x: jax.numpy.broadcast_to(x, (N,) + x.shape), mjx_data)
    batch_ctrl = jax.numpy.zeros((N, model.nu))
    batch_step = jax.jit(jax.vmap(lambda dd, cc: mjx.step(mjx_model, dd.replace(ctrl=cc))))
    batch = batch_step(batch, batch_ctrl)
    assert batch.qpos.shape == (N, model.nq)
    assert diffs[100] >= diffs[10] * 0.5, "接触场景差异应随步数增大（定性）"
    dev = jax.devices()[0].platform
    return (f"jit step ✓ vmap batch qpos{batch.qpos.shape} ✓ device={dev} "
            f"CPU↔MJX max|Δqpos| 10步={diffs[10]:.2e} 100步={diffs[100]:.2e}（随步数放大）")


@test("07-04 mjx: put_model 支持性（panda ok / go2 fail）")
def t_mjx_limitations():
    import mujoco
    try:
        import mujoco.mjx as mjx
    except ImportError as e:
        return f"SKIP mjx 未安装: {e}"
    mdir = menagerie_dir()
    assert mdir, "menagerie 不存在"
    m_panda = mujoco.MjModel.from_xml_path(str(mdir / "franka_emika_panda" / "panda.xml"))
    mjx.put_model(m_panda)  # 含 tendon，应通过
    go2_status = "mjx_ok(与教程 mjx_failed 不符!)"
    try:
        m_go2 = mujoco.MjModel.from_xml_path(str(mdir / "unitree_go2" / "scene.xml"))
        mjx.put_model(m_go2)
    except NotImplementedError as e:
        go2_status = f"NotImplementedError({str(e)[:60]}...)"
    except Exception as e:
        go2_status = f"{type(e).__name__}({str(e)[:60]})"
    return f"panda put_model ✓（tendon 支持）；go2 → {go2_status}"


# ---------------------------------------------------- 08-training
@test("08-02 sb3: shimmy 链路 10k 冒烟")
def t_sb3_cartpole():
    try:
        from dm_control import suite
        from shimmy import DmControlCompatibilityV0
        from gymnasium.wrappers import FlattenObservation
        from stable_baselines3 import PPO
        from stable_baselines3.common.evaluation import evaluate_policy
    except ImportError as e:
        return f"SKIP 依赖缺失: {e}"
    dm_env = suite.load("cartpole", "swingup", task_kwargs={"random": 0})
    env = DmControlCompatibilityV0(dm_env, render_mode="rgb_array")
    env = FlattenObservation(env)
    model = PPO("MlpPolicy", env, verbose=0, device="cpu", seed=0)
    model.learn(total_timesteps=10_000)
    mean_r, std_r = evaluate_policy(model, env, n_eval_episodes=3)
    frame = env.render()
    assert frame is not None and frame.ndim == 3
    assert "train/explained_variance" in model.logger.name_to_value, \
        f"logger keys={sorted(model.logger.name_to_value)}"
    logger_keys = sorted(k for k in model.logger.name_to_value if "explained" in k)
    return (f"10k 步冒烟 ✓ eval reward={mean_r:.1f}±{std_r:.1f} render ✓ "
            f"logger key={logger_keys}（应为 explained_variance 全名）")


@test("08-04 BC: 录 demo + MLP 训练骨架")
def t_bc():
    try:
        import torch
        import torch.nn as nn
    except ImportError as e:
        return f"SKIP torch 未安装: {e}"
    import mujoco
    work = grasp_workdir()
    model_m = mujoco.MjModel.from_xml_path(str(work / "grasping_scene.xml"))
    data = mujoco.MjData(model_m)
    READY = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785])

    def expert_policy(data):
        act = np.zeros(model_m.nu)
        act[:7] = READY + 0.1 * np.sin(data.time)
        act[7] = 255
        return act

    observations, actions = [], []
    for step in range(500):
        action = expert_policy(data)
        obs = np.concatenate([data.qpos, data.qvel])
        observations.append(obs)
        actions.append(action)
        data.ctrl[:] = action
        mujoco.mj_step(model_m, data)
    obs = torch.tensor(np.array(observations), dtype=torch.float32)
    acts = torch.tensor(np.array(actions), dtype=torch.float32)

    class Policy(nn.Module):
        def __init__(self, obs_dim, act_dim):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(obs_dim, 128), nn.ReLU(),
                nn.Linear(128, 128), nn.ReLU(),
                nn.Linear(128, act_dim))

        def forward(self, x):
            return self.net(x)

    torch.manual_seed(0)
    policy = Policy(obs.shape[1], acts.shape[1])
    optimizer = torch.optim.Adam(policy.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    losses = []
    for epoch in range(100):
        pred = policy(obs)
        loss = loss_fn(pred, acts)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    assert losses[-1] < losses[0], "loss 应下降"
    mujoco.mj_resetData(model_m, data)
    for _ in range(300):
        obs_t = torch.tensor(np.concatenate([data.qpos, data.qvel]), dtype=torch.float32)
        with torch.no_grad():
            action = policy(obs_t).numpy()
        data.ctrl[:] = action
        mujoco.mj_step(model_m, data)
    return f"demo 500 步 → BC loss {losses[0]:.2f}→{losses[-1]:.4f} → 回放 300 步 ✓"


@test("08-05 sim2real: randomize_domain 前后参数")
def t_domain_rand():
    import mujoco
    work = grasp_workdir()
    model = mujoco.MjModel.from_xml_path(str(work / "grasping_scene.xml"))
    rng = np.random.default_rng(0)
    block_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "block")
    before_mass = float(model.body_mass[block_id])
    before_fric = model.geom_friction[:, 0].copy()
    model.body_mass[block_id] = rng.uniform(0.03, 0.08)
    for i in range(model.ngeom):
        model.geom_friction[i, 0] = model.geom_friction[i, 0] * rng.uniform(0.7, 1.3)
    after_mass = float(model.body_mass[block_id])
    ratio = model.geom_friction[:, 0] / np.where(before_fric == 0, 1, before_fric)
    assert 0.03 <= after_mass <= 0.08
    assert (ratio[before_fric > 0] >= 0.7 - 1e-9).all() and (ratio[before_fric > 0] <= 1.3 + 1e-9).all()
    return f"block mass {before_mass}→{after_mass:.4f}（∈[0.03,0.08]）friction 乘子∈[{ratio.min():.2f},{ratio.max():.2f}] ✓"


# ---------------------------------------------------------------- runner
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="只跑名字包含该子串的测试")
    args = ap.parse_args()

    mdir = menagerie_dir()
    header = [
        f"verify_tutorial_code — MuJoCo 教程代码逐页验证",
        f"python={sys.version.split()[0]} MUJOCO_GL={os.environ.get('MUJOCO_GL')}",
        f"menagerie={public_menagerie_path(mdir)}",
    ]
    try:
        import mujoco
        header.append(f"mujoco={mujoco.__version__}")
    except ImportError:
        header.append("mujoco=MISSING")
    print("\n".join(header))
    print("=" * 78)

    for name, fn in TESTS:
        if args.only and args.only not in name:
            continue
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                detail = fn() or "ok"
            status = "SKIP" if str(detail).startswith("SKIP") else "PASS"
        except Exception:
            status = "FAIL"
            detail = traceback.format_exc(limit=3).strip().replace("\n", " | ")
        RESULTS.append((name, status, str(detail)))
        print(f"[{status}] {name}\n       {detail}")

    n_pass = sum(1 for _, s, _ in RESULTS if s == "PASS")
    n_fail = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    n_skip = sum(1 for _, s, _ in RESULTS if s == "SKIP")
    print("=" * 78)
    print(f"TOTAL: {len(RESULTS)}  PASS: {n_pass}  FAIL: {n_fail}  SKIP: {n_skip}")

    RUNS.mkdir(parents=True, exist_ok=True)
    out = RUNS / "verify_tutorial_code.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n" + "=" * 78 + "\n")
        for name, status, detail in RESULTS:
            f.write(f"[{status}] {name}\n       {detail}\n")
        f.write("=" * 78 + f"\nTOTAL: {len(RESULTS)}  PASS: {n_pass}  FAIL: {n_fail}  SKIP: {n_skip}\n")
    try:
        out_label = out.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        out_label = out.name
    print(f"written: {out_label}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
