"""Inspect or repair USD articulation roots before using an asset in Isaac Lab.

MJCF conversion can generate more than one ``UsdPhysics.ArticulationRootAPI``
under the same asset. Isaac Lab's ``Articulation`` expects exactly one
articulation root under the configured prim path. This small tool makes that
failure explicit and can write a repaired copy by keeping one selected root.

Examples:

    ./isaaclab.sh -p labs/06_isaac_lab/repair_usd_articulation_roots.py --usd robot.usd --headless

    ./isaaclab.sh -p labs/06_isaac_lab/repair_usd_articulation_roots.py \
        --usd robot.usd \
        --output robot_single_root.usd \
        --keep-root /robot/base/base \
        --headless
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Inspect or repair USD articulation roots.")
parser.add_argument("--usd", required=True, help="Input USD file.")
parser.add_argument("--output", default=None, help="Optional repaired USD output path.")
parser.add_argument("--keep-root", default=None, help="Articulation root path to keep when writing --output.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, UsdPhysics  # noqa: E402


def find_articulation_roots(stage: Usd.Stage) -> list[str]:
    """Return all prim paths with ArticulationRootAPI."""
    roots: list[str] = []
    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            roots.append(str(prim.GetPath()))
    return roots


def main() -> None:
    input_path = Path(args_cli.usd).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"USD file does not exist: {input_path}")

    target_path = input_path
    if args_cli.output:
        target_path = Path(args_cli.output).expanduser().resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(input_path, target_path)

    stage = Usd.Stage.Open(str(target_path))
    if stage is None:
        raise RuntimeError(f"Failed to open USD stage: {target_path}")

    roots = find_articulation_roots(stage)
    print(f"USD: {target_path}")
    print(f"Articulation root count: {len(roots)}")
    for root in roots:
        print(f"  - {root}")

    if not args_cli.output:
        if len(roots) != 1:
            raise RuntimeError(
                "Expected exactly one articulation root. Re-run with --output and --keep-root "
                "to write a repaired copy."
            )
        return

    if not args_cli.keep_root:
        raise ValueError("--keep-root is required when --output is provided.")
    if args_cli.keep_root not in roots:
        raise ValueError(f"--keep-root {args_cli.keep_root!r} is not one of: {roots}")

    removed: list[str] = []
    for root in roots:
        if root == args_cli.keep_root:
            continue
        prim = stage.GetPrimAtPath(root)
        prim.RemoveAPI(UsdPhysics.ArticulationRootAPI)
        removed.append(root)

    stage.GetRootLayer().Save()

    repaired_roots = find_articulation_roots(stage)
    print("Removed articulation roots:")
    for root in removed:
        print(f"  - {root}")
    print(f"Repaired articulation root count: {len(repaired_roots)}")
    for root in repaired_roots:
        print(f"  - {root}")

    if repaired_roots != [args_cli.keep_root]:
        raise RuntimeError(f"Repair did not leave exactly the requested root: {repaired_roots}")


if __name__ == "__main__":
    main()
    simulation_app.close(wait_for_replicator=False, skip_cleanup=True)
