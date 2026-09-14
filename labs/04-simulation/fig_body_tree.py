"""4.2 — Figure: Panda body tree.

Renders the full Panda (home pose) and dumps its body tree as ASCII. Source for
the body-tree figure in the modeling chapter.

Menagerie location: $MUJOCO_MENAGERIE if set, else reference/mujoco_menagerie.

Run:
    MUJOCO_GL=egl python labs/04-simulation/fig_body_tree.py

Outputs:
    runs/04-simulation/fig_body_tree.png
    runs/04-simulation/fig_body_tree.txt
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

try:
    import mujoco
except ImportError as exc:
    raise RuntimeError("mujoco missing; pip install mujoco>=3.0") from exc

try:
    import imageio.v3 as iio
except ImportError as exc:
    raise RuntimeError("imageio[ffmpeg] missing; pip install 'imageio[ffmpeg]'") from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

MENAGERIE = Path(os.environ.get("MUJOCO_MENAGERIE", ROOT / "reference" / "mujoco_menagerie"))
PANDA_SCENE = MENAGERIE / "franka_emika_panda" / "scene.xml"


def render_panda() -> None:
    model = mujoco.MjModel.from_xml_path(str(PANDA_SCENE))
    data = mujoco.MjData(model)
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    with mujoco.Renderer(model, height=480, width=640) as r:
        r.update_scene(data, camera=-1)
        img = r.render()
    out = RUNS / "fig_body_tree.png"
    iio.imwrite(str(out), img)
    print(f"[write] {out}")


def dump_tree() -> None:
    model = mujoco.MjModel.from_xml_path(str(PANDA_SCENE))
    lines = [f"model: {PANDA_SCENE.name}", f"  nbody = {model.nbody}", "",
             "BODY TREE (id  name  parent  mass)"]
    children: dict[int, list[int]] = {i: [] for i in range(model.nbody)}
    for i in range(1, model.nbody):
        children[int(model.body_parentid[i])].append(i)

    def walk(node: int, depth: int) -> None:
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, node) or "<unnamed>"
        mass = float(model.body_mass[node])
        indent = "  " * depth
        lines.append(f"  {node:3d}  {indent}{name:30s}  {int(model.body_parentid[node]):3d}  {mass:.4f}")
        for c in children[node]:
            walk(c, depth + 1)

    walk(0, 0)
    text = "\n".join(lines) + "\n"
    (RUNS / "fig_body_tree.txt").write_text(text)
    print(text)


def main() -> None:
    if not PANDA_SCENE.exists():
        raise SystemExit(f"Panda scene not found at {PANDA_SCENE} "
                         f"(set MUJOCO_MENAGERIE or clone into reference/)")
    render_panda()
    dump_tree()


if __name__ == "__main__":
    main()
