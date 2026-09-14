"""4.5 — mujoco_menagerie tour: inventory and load-test every robot.

Scans ``$MUJOCO_MENAGERIE`` or ``reference/mujoco_menagerie`` for
top-level robot directories, tries to load each scene XML, and renders a
single thumbnail per robot into
``runs/04-simulation/menagerie/<robot>.png``.

Two output channels:
  - ``menagerie_tour.json`` — full per-robot status (loaded, nq, nu, error)
  - ``menagerie_tour.txt``  — human-readable summary table

If ``reference/mujoco_menagerie/`` is empty the script still runs (and
writes a stub JSON) so the html page can link a deterministic placeholder.

Run:
    MUJOCO_GL=egl python labs/04-simulation/menagerie_tour.py

To restrict to a few robots:
    MUJOCO_GL=egl python labs/04-simulation/menagerie_tour.py \
        --robots franka_emika_panda universal_robots_ur5e unitree_a1
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

os.environ.setdefault("MUJOCO_GL", "egl")

try:
    import mujoco
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("mujoco missing; install via `pip install mujoco>=3.0`") from exc

try:
    import imageio.v3 as iio
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "imageio[ffmpeg] missing; install via `pip install 'imageio[ffmpeg]'`"
    ) from exc

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)
THUMBS = RUNS / "menagerie"
THUMBS.mkdir(parents=True, exist_ok=True)

MENAGERIE_ENV = os.environ.get("MUJOCO_MENAGERIE")
MENAGERIE = (
    Path(MENAGERIE_ENV).expanduser()
    if MENAGERIE_ENV
    else ROOT / "reference" / "mujoco_menagerie"
)

# Robots to highlight if no --robots filter is given. These are the
# "headline" arms / humanoids / quadrupeds people typically reach for.
HIGHLIGHT = [
    "franka_emika_panda",
    "universal_robots_ur5e",
    "kuka_iiwa_14",
    "unitree_a1",
    "unitree_go2",
    "anybotics_anymal_b",
    "anybotics_anymal_c",
    "aloha",
    "trs_so_arm100",  # SO-ARM-100 (open-source 6-DoF arm) if present
    "robotis_op3",
    "google_robot",
]


def public_menagerie_path(path: Path | None = None) -> str:
    """Return a portable path for committed reports."""
    base = "$MUJOCO_MENAGERIE" if MENAGERIE_ENV else "reference/mujoco_menagerie"
    if path is None:
        return base
    try:
        relative = path.resolve().relative_to(MENAGERIE.resolve())
    except ValueError:
        return path.name
    return f"{base}/{relative.as_posix()}" if relative.parts else base


def public_message(message: str) -> str:
    return message.replace(str(MENAGERIE), public_menagerie_path())


def load_xml_candidate(robot_dir: Path) -> Path | None:
    """Return the most likely "scene" XML for a menagerie robot."""
    # Prefer scene.xml; fall back to a model named like the robot, then any .xml
    candidates = [
        robot_dir / "scene.xml",
        robot_dir / f"{robot_dir.name}.xml",
        *sorted(robot_dir.glob("scene_*.xml")),
        *sorted(robot_dir.glob("*.xml")),
    ]
    for c in candidates:
        if c.exists() and not c.name.startswith("mjx_"):
            return c
    return None


def render_thumbnail(model: mujoco.MjModel, out_path: Path) -> str | None:
    data = mujoco.MjData(model)
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    try:
        with mujoco.Renderer(model, height=240, width=320) as r:
            r.update_scene(data, camera=-1)
            img = r.render()
        iio.imwrite(str(out_path), img)
        return None
    except Exception as exc:  # pragma: no cover - render errors are common headless
        return f"{type(exc).__name__}: {exc!s}"[:200]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--robots", nargs="*", default=None, help="Limit to specific robot dirs")
    args = parser.parse_args()

    if not MENAGERIE.exists() or not any(MENAGERIE.iterdir()):
        stub = {
            "status": "menagerie not cloned",
            "menagerie_path": public_menagerie_path(),
            "hint": "Tarball download: curl -L https://codeload.github.com/google-deepmind/mujoco_menagerie/tar.gz/refs/heads/main -o m.tgz && tar xzf m.tgz -C reference/ && mv reference/mujoco_menagerie-main reference/mujoco_menagerie",
        }
        (RUNS / "menagerie_tour.json").write_text(json.dumps(stub, indent=2))
        (RUNS / "menagerie_tour.txt").write_text(
            "menagerie not cloned; see hint in menagerie_tour.json\n"
        )
        print(json.dumps(stub, indent=2))
        return

    # Detect available robot dirs.
    all_dirs = sorted(p.name for p in MENAGERIE.iterdir() if p.is_dir() and not p.name.startswith("."))
    if args.robots:
        targets = [r for r in args.robots if r in all_dirs]
        missing = [r for r in args.robots if r not in all_dirs]
    else:
        targets = [r for r in HIGHLIGHT if r in all_dirs]
        # Add a sample of other robots if we have fewer than 8 highlights present.
        extras = [r for r in all_dirs if r not in targets]
        if len(targets) < 8:
            targets.extend(extras[: 8 - len(targets)])
        missing = []

    results = []
    for robot in targets:
        rdir = MENAGERIE / robot
        xml = load_xml_candidate(rdir)
        entry: dict = {
            "robot": robot,
            "xml": public_menagerie_path(xml) if xml else None,
        }
        if xml is None:
            entry["status"] = "no scene.xml found"
            results.append(entry)
            continue
        try:
            model = mujoco.MjModel.from_xml_path(str(xml))
            entry.update(
                status="loaded",
                nq=int(model.nq),
                nv=int(model.nv),
                nu=int(model.nu),
                nbody=int(model.nbody),
                ngeom=int(model.ngeom),
            )
            thumb = THUMBS / f"{robot}.png"
            err = render_thumbnail(model, thumb)
            if err:
                entry["render"] = public_message(err)
            else:
                entry["thumbnail"] = thumb.relative_to(ROOT).as_posix()
        except Exception as exc:
            entry["status"] = "load_error"
            entry["error"] = public_message(
                f"{type(exc).__name__}: {exc!s}"
            )[:240]
        results.append(entry)

    # Per-robot summary table.
    table = ["robot                          status     nq   nu   nbody  thumb"]
    table.append("-" * 78)
    for r in results:
        nq = r.get("nq", "-")
        nu = r.get("nu", "-")
        nb = r.get("nbody", "-")
        thumb = "ok" if "thumbnail" in r else r.get("render", "skip")[:18]
        table.append(f"{r['robot']:30s} {r['status']:10s} {str(nq):>3} {str(nu):>3} {str(nb):>5}   {thumb}")

    summary = "\n".join(table)
    menagerie_label = public_menagerie_path()
    print(f"menagerie path: {menagerie_label}")
    print(f"available robots: {len(all_dirs)}")
    print(summary)
    if missing:
        print(f"requested but missing: {missing}")

    (RUNS / "menagerie_tour.txt").write_text(
        f"menagerie path: {menagerie_label}\n"
        f"available robots: {len(all_dirs)}\n\n{summary}\n"
    )
    (RUNS / "menagerie_tour.json").write_text(
        json.dumps(
            {
                "mujoco_version": mujoco.__version__,
                "menagerie_path": menagerie_label,
                "available_robots": all_dirs,
                "targets": targets,
                "results": results,
                "thumbnails_dir": THUMBS.relative_to(ROOT).as_posix(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
