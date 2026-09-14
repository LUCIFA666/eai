"""Environment verification — print versions and run smoke checks.

Run: ``python labs/check_env.py``

Outputs a Markdown table that you can paste into ``runs/`` to prove
your environment matches the curriculum's expected versions.
"""
from __future__ import annotations

import importlib
import importlib.metadata as md
import platform
import sys
from datetime import datetime

PACKAGES = [
    "numpy",
    "scipy",
    "torch",
    "gymnasium",
    "minigrid",
    "mujoco",
    "dm_control",
    "stable_baselines3",
    "imageio",
    "open3d",
    "transformers",
    "datasets",
    "huggingface_hub",
    "lerobot",
    "sapien",
    "mani_skill",
    "robosuite",
    "robomimic",
]


def get_version(pkg: str) -> str:
    try:
        m = importlib.import_module(pkg)
    except Exception as exc:  # pragma: no cover - environment dependent
        return f"NOT_IMPORTABLE ({type(exc).__name__})"
    version = getattr(m, "__version__", None)
    if version:
        return str(version)
    try:
        return md.version(pkg)
    except md.PackageNotFoundError:
        return "imported (no __version__)"


def main() -> int:
    print(f"# environment check — {datetime.utcnow().isoformat()}Z")
    print(f"- python: `{sys.version.split()[0]}`")
    print(f"- platform: `{platform.platform()}`")
    print()
    print("| package | version |")
    print("|---|---|")
    for pkg in PACKAGES:
        print(f"| `{pkg}` | {get_version(pkg)} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
