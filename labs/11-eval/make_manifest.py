"""11.1 — Build a run manifest from the current environment.

Records: task, command, git SHA + dirty bit, python/platform/GPU,
pinned package versions, seed, and output paths.  Deterministic for
the same git tree (excluding the created_at field).

Run:
    python labs/11-eval/make_manifest.py
Output:
    runs/11-eval/manifest_example.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as im
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULTS = {
    "seed": 0,
    "task": "cartpole_pd_smoke",
    "command": "python labs/11-eval/make_manifest.py --seed 0",
    "metrics_path": "runs/11-eval/metrics_example.json",
    "video_path": "runs/11-eval/episode_0.mp4",
}

ALLOWLIST = ("numpy", "torch", "gymnasium", "imageio", "imageio-ffmpeg", "pyyaml")


def _git(args: list[str]) -> str:
    try:
        out = subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return ""


def _gpu() -> list[dict]:
    if shutil.which("nvidia-smi") is None:
        return []
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,driver_version",
             "--format=csv,noheader,nounits"], timeout=5,
        ).decode().strip()
    except Exception:
        return []
    rows = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 4:
            rows.append({"index": int(parts[0]), "name": parts[1],
                         "memory_mb": int(parts[2]), "driver": parts[3]})
    return rows


def _packages(names: tuple[str, ...]) -> dict[str, str]:
    out: dict[str, str] = {}
    for n in names:
        try: out[n] = im.version(n)
        except im.PackageNotFoundError: out[n] = "not-installed"
    return out


def build_manifest(seed: int, task: str, command: str,
                   metrics_path: str, video_path: str) -> dict:
    payload = {
        "schema_version": "1.0", "task": task, "seed": int(seed),
        "command": command,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code": {"git_sha": _git(["rev-parse", "HEAD"]),
                  "git_branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]),
                  "git_dirty": bool(_git(["status", "--porcelain"]))},
        "env":  {"python": sys.version.split()[0],
                  "platform": platform.platform(),
                  "implementation": platform.python_implementation(),
                  "gpu": _gpu()},
        "packages": _packages(ALLOWLIST),
        "outputs": {"metrics_path": metrics_path, "video_path": video_path},
    }
    # stable identity hash (excluding wall-clock time)
    identity = {k: v for k, v in payload.items() if k != "created_at"}
    payload["content_hash"] = hashlib.sha256(
        json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return payload


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=DEFAULTS["seed"])
    p.add_argument("--task", default=DEFAULTS["task"])
    p.add_argument("--command", default=DEFAULTS["command"])
    p.add_argument("--metrics-path", default=DEFAULTS["metrics_path"])
    p.add_argument("--video-path", default=DEFAULTS["video_path"])
    p.add_argument("--out", default="runs/11-eval/manifest_example.json")
    a = p.parse_args()
    m = build_manifest(a.seed, a.task, a.command, a.metrics_path, a.video_path)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(m, indent=2, ensure_ascii=False))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
