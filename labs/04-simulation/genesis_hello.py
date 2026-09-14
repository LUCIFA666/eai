"""Genesis 入门：创建场景、加载机器人、PD 控制并记录关节轨迹。

用法：
    conda activate labgenesis
    python labs/04-simulation/genesis_hello.py

输出：
    runs/genesis_hello_info.txt       场景和关节信息
    runs/genesis_joint_trajectory.csv 关节轨迹数据
"""

import os

os.environ["DISPLAY"] = ""

import genesis as gs
import numpy as np

OUTDIR = os.path.join(os.path.dirname(__file__), "..", "..", "runs")
os.makedirs(OUTDIR, exist_ok=True)

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    show_viewer=False,
)

plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

dof_names = [franka.joints[i].name for i in range(franka.n_dofs)]
n_dofs = franka.n_dofs

lines = [
    "=== Genesis Hello World ===",
    f"Genesis version : {gs.__version__}",
    f"Backend         : cpu",
    f"Scene entities  : {len(scene.entities)}",
    f"Robot name      : franka_emika_panda",
    f"DoFs            : {n_dofs}",
    f"Joint names     : {dof_names}",
    "",
    "--- Initial joint positions ---",
]
qpos = franka.get_dofs_position().cpu().numpy()
for i, name in enumerate(dof_names):
    lines.append(f"  {name:30s} = {qpos[i]:.4f}")

# --- PD control: move to a target configuration ---
target = np.array([0.0, -0.3, 0.0, -1.5, 0.0, 1.2, 0.8, 0.04, 0.04])

arm_dof_idx = list(range(7))
franka.set_dofs_kp(np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]))
franka.set_dofs_kv(np.array([450, 450, 350, 350, 200, 200, 200, 10, 10]))

lines.append("")
lines.append(f"--- PD control to target (500 steps, dt=0.01) ---")
lines.append(f"Target: {target.tolist()}")

trajectory = []
for step in range(500):
    franka.control_dofs_position(target)
    scene.step()
    qpos_now = franka.get_dofs_position().cpu().numpy()
    if step % 10 == 0:
        trajectory.append([step * 0.01] + qpos_now.tolist())

qpos_final = franka.get_dofs_position().cpu().numpy()
lines.append("")
lines.append("--- Final joint positions ---")
for i, name in enumerate(dof_names):
    err = abs(qpos_final[i] - target[i])
    lines.append(f"  {name:30s} = {qpos_final[i]:+.4f}  (target {target[i]:+.4f}, err {err:.4f})")

# Save info
info_path = os.path.join(OUTDIR, "genesis_hello_info.txt")
with open(info_path, "w") as f:
    f.write("\n".join(lines))

# Save trajectory CSV
csv_path = os.path.join(OUTDIR, "genesis_joint_trajectory.csv")
header = "time," + ",".join(dof_names)
with open(csv_path, "w") as f:
    f.write(header + "\n")
    for row in trajectory:
        f.write(",".join(f"{v:.6f}" for v in row) + "\n")

print("\n".join(lines))
print(f"\nInfo saved to {info_path}")
print(f"Trajectory saved to {csv_path} ({len(trajectory)} rows)")
