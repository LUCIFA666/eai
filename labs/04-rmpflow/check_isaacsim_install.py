"""Minimal Isaac Sim 4.5 and motion-generation import check."""

from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        from isaacsim import SimulationApp
    except ImportError as exc:
        print(f"[FAIL] cannot import isaacsim: {exc}", file=sys.stderr)
        return 2

    app = SimulationApp({"headless": args.headless})
    try:
        import isaacsim.robot_motion.motion_generation as motion_generation
        from isaacsim.robot_motion.motion_generation.interface_config_loader import (
            get_supported_robot_policy_pairs,
        )

        pairs = get_supported_robot_policy_pairs()
        print("python:", sys.version.split()[0])
        print("motion_generation:", motion_generation.__name__)
        print("supported robots:", sorted(pairs))
        if "Franka" not in pairs:
            print("[FAIL] Franka configuration is unavailable", file=sys.stderr)
            return 3
        print("[OK] Isaac Sim and RMPflow configuration loader are available")
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
