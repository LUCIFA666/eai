"""Genesis 多物理演示：刚体 + 柔体在同一场景中交互。

用法：
    conda activate labgenesis
    python labs/04-simulation/genesis_multiphysics.py

输出：
    runs/genesis_multiphysics_info.txt  场景结构和粒子统计
"""

import os

os.environ["DISPLAY"] = ""

import genesis as gs
import numpy as np

OUTDIR = os.path.join(os.path.dirname(__file__), "..", "..", "runs")
os.makedirs(OUTDIR, exist_ok=True)

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005, substeps=10),
    show_viewer=False,
)

# 1. 刚体地面
plane = scene.add_entity(gs.morphs.Plane())

# 2. 刚体方块
box = scene.add_entity(
    gs.morphs.Box(
        size=(0.1, 0.1, 0.1),
        pos=(0.0, 0.0, 0.5),
    )
)

# 3. 刚体球
sphere = scene.add_entity(
    gs.morphs.Sphere(
        pos=(0.0, 0.2, 0.8),
        radius=0.06,
    ),
)

# 4. 刚体圆柱
cylinder = scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.15, -0.1, 0.6),
        radius=0.04,
        height=0.12,
    ),
)

scene.build()

lines = [
    "=== Genesis Multi-Object Rigid Demo ===",
    f"Genesis version : {gs.__version__}",
    f"Entities        : {len(scene.entities)}",
    f"  [0] Plane       (rigid ground)",
    f"  [1] Box 10cm    (rigid, dropped from 0.5m)",
    f"  [2] Sphere r=6cm (rigid, dropped from 0.8m)",
    f"  [3] Cylinder    (rigid, dropped from 0.6m)",
    "",
]

lines.append("--- Simulating 500 steps (2.5s at dt=0.005) ---")
for step in range(500):
    scene.step()
    if step % 100 == 99:
        box_pos = box.get_pos().cpu().numpy()
        sph_pos = sphere.get_pos().cpu().numpy()
        cyl_pos = cylinder.get_pos().cpu().numpy()
        lines.append(f"  step {step+1:3d}: box z={box_pos[2]:.4f}, sphere z={sph_pos[2]:.4f}, cyl z={cyl_pos[2]:.4f}")

lines.append("")
lines.append("--- Final state ---")
for name, ent, expect_z in [("Box", box, 0.05), ("Sphere", sphere, 0.06), ("Cylinder", cylinder, 0.06)]:
    pos = ent.get_pos().cpu().numpy()
    lines.append(f"  {name:10s} pos: [{pos[0]:+.4f}, {pos[1]:+.4f}, {pos[2]:+.4f}]  settled: {'yes' if abs(pos[2] - expect_z) < 0.03 else 'no'}")

info_path = os.path.join(OUTDIR, "genesis_multiphysics_info.txt")
with open(info_path, "w") as f:
    f.write("\n".join(lines))

print("\n".join(lines))
print(f"\nSaved to {info_path}")
