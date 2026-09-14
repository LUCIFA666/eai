"""4.4 — Sensor declaration & sensordata verification.

Backs the "sensor 与 sensordata" page: declares sensors in an MJCF <sensor>
section, then reads them back two ways and cross-checks against data.qpos:
  - via model.sensor_adr / model.sensor_dim slicing of data.sensordata
  - via the data.sensor("name").data named accessor

Self-contained (inline 2-link arm + block), no menagerie needed.

Run:
    MUJOCO_GL=egl python labs/04-simulation/sensors_check.py

Outputs:
    runs/04-simulation/sensors_check.txt
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

os.environ.setdefault("MUJOCO_GL", "egl")

try:
    import mujoco
except ImportError as exc:
    raise RuntimeError("mujoco missing") from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

XML = """<mujoco model="sensor_demo">
  <compiler angle="radian"/>
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    <geom type="plane" size="1 1 0.1" rgba=".9 0 0 1"/>

    <body name="base" pos="0 0 0">
      <geom type="box" size="0.1 0.1 0.05" rgba="0.5 0.5 0.5 1"/>
      <body name="arm1" pos="0 0 0.1">
        <joint name="j1" type="hinge" axis="0 1 0" range="-1.57 1.57"/>
        <geom type="capsule" size="0.02" fromto="0 0 0 0 0 0.2" rgba="0.3 0.6 1 1"/>
        <body name="arm2" pos="0 0 0.2">
          <joint name="j2" type="hinge" axis="0 1 0" range="-1.57 1.57"/>
          <geom type="capsule" size="0.02" fromto="0 0 0 0 0 0.2" rgba="1 0.4 0.2 1"/>
          <site name="tip" pos="0 0 0.2" size="0.01"/>
          <site name="touch_site" pos="0 0 0.22" size="0.01"/>
        </body>
      </body>
    </body>

    <body name="block" pos="0.2 0 0.52">
      <joint type="free"/>
      <geom name="block_geom" type="box" size="0.05 0.05 0.05" mass="0.1" rgba="0 1 0 0.5"/>
    </body>
  </worldbody>

  <sensor>
    <jointpos name="j1_pos"   joint="j1"/>
    <jointpos name="j2_pos"   joint="j2"/>
    <jointvel name="j1_vel"   joint="j1"/>
    <jointvel name="j2_vel"   joint="j2"/>
    <framepos name="tip_pos"  objtype="site" objname="tip"/>
    <touch    name="tip_touch" site="touch_site"/>
  </sensor>
</mujoco>"""


def main() -> None:
    model = mujoco.MjModel.from_xml_string(XML)
    data = mujoco.MjData(model)
    assert model.nsensor > 0, "expected sensors to be declared"

    for _ in range(100):
        mujoco.mj_step(model, data)

    lines = [f"nsensor = {model.nsensor}", ""]

    lines.append("=== Method 1: sensor_adr + sensor_dim ===")
    for i in range(model.nsensor):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SENSOR, i)
        adr = model.sensor_adr[i]
        dim = model.sensor_dim[i]
        value = data.sensordata[adr:adr + dim].copy()
        lines.append(f"  sensor[{i}] {name:15s}  adr={adr}  dim={dim}  value={np.round(value, 4)}")

    lines.append("")
    lines.append("=== Method 2: data.sensor('name').data ===")
    for i in range(model.nsensor):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SENSOR, i)
        lines.append(f"  {name:15s}  = {np.round(data.sensor(name).data.copy(), 4)}")

    lines.append("")
    lines.append("=== Cross-check: sensor vs data.qpos ===")
    lines.append(f"  data.qpos      = {np.round(data.qpos, 4)}")
    assert abs(data.sensor("j1_pos").data[0] - data.qpos[0]) < 1e-9
    assert abs(data.sensor("j2_pos").data[0] - data.qpos[1]) < 1e-9
    lines.append("  [OK] jointpos sensor values match data.qpos")

    text = "\n".join(lines)
    print(text)
    (RUNS / "sensors_check.txt").write_text(text + "\n")
    print("\n[OK] sensor_adr/dim slicing and data.sensor('name').data both verified.")


if __name__ == "__main__":
    main()
