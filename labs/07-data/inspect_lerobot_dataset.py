"""7.1 - Inspect the structure of a LeRobotDataset.

Strategy:
  1. Try the high-level ``LeRobotDataset`` loader. It downloads to
     ``~/.cache/huggingface/lerobot/<repo>``. This call may fail if the
     installed lerobot has an import bug (we saw GR00T config dataclass
     errors in lerobot==0.4.4) or if torchcodec can't decode mp4s.
  2. Fall back to reading the on-disk parquet + json files directly with
     pyarrow + json. That's enough to expose the dataset schema.
  3. If even (2) fails (offline / no auth / never fetched), print the
     documented layout from the LeRobotDataset docstring and write
     ``runs/07-data/dataset_inspect.skipped`` so the chapter HTML can
     render a "skipped" badge.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/07-data/inspect_lerobot_dataset.py
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

OUT_DIR = Path("runs/07-data")
OUT_DIR.mkdir(parents=True, exist_ok=True)

REPO_ID = "lerobot/pusht"
CACHE_ROOT = Path(os.environ.get("LEROBOT_HOME",
                                 Path.home() / ".cache/huggingface/lerobot"))


def documented_layout() -> str:
    return (
        "Documented LeRobotDataset (v3) layout (from\n"
        "  reference/lerobot/src/lerobot/datasets/lerobot_dataset.py docstring):\n"
        ".\n"
        "├── data/\n"
        "│   └── chunk-000/file-000.parquet ...   # action + state columns\n"
        "├── meta/\n"
        "│   ├── episodes/chunk-000/file-000.parquet  # one row per episode\n"
        "│   ├── info.json                            # shapes, fps, codebase_version\n"
        "│   ├── stats.json                           # mean/std for normalisation\n"
        "│   └── tasks.parquet                        # task descriptions\n"
        "└── videos/\n"
        "    └── observation.images.<cam>/chunk-000/file-000.mp4\n"
    )


def parquet_summary(path: Path, head: int = 3) -> dict:
    try:
        import pyarrow.parquet as pq
        tbl = pq.read_table(path)
    except Exception as e:  # noqa: BLE001
        return {"error": repr(e)}
    sample_rows = tbl.slice(0, head).to_pylist()
    # truncate long lists to keep printable
    for row in sample_rows:
        for k, v in list(row.items()):
            if isinstance(v, (list, tuple)) and len(v) > 6:
                row[k] = f"<list len={len(v)} first6={list(v[:6])}>"
            elif hasattr(v, "shape"):
                row[k] = f"<array shape={v.shape} dtype={v.dtype}>"
    return {
        "num_rows": tbl.num_rows,
        "columns": [{"name": c, "type": str(tbl.schema.field(c).type)}
                    for c in tbl.column_names],
        "sample_rows_first3": sample_rows,
    }


def offline_inspect() -> dict | None:
    root = CACHE_ROOT / REPO_ID
    if not root.exists():
        return None
    info_path = root / "meta" / "info.json"
    out: dict = {"repo_id": REPO_ID, "status": "offline_ok",
                 "root": str(root), "files_listed": []}
    if info_path.exists():
        info = json.loads(info_path.read_text())
        out["info_json"] = {
            "codebase_version": info.get("codebase_version"),
            "fps": info.get("fps"),
            "total_episodes": info.get("total_episodes"),
            "total_frames": info.get("total_frames"),
            "total_videos": info.get("total_videos"),
            "feature_keys": list(info.get("features", {}).keys()),
            "features_sample": {
                k: {sk: sv for sk, sv in v.items() if sk in ("dtype", "shape", "names")}
                for k, v in list(info.get("features", {}).items())[:6]
            },
        }
    stats_path = root / "meta" / "stats.json"
    if stats_path.exists():
        stats = json.loads(stats_path.read_text())
        out["stats_json_keys"] = list(stats.keys())[:8]
    data_parquet = next((root / "data").rglob("*.parquet"), None)
    if data_parquet is not None:
        out["data_parquet"] = {"path": str(data_parquet.relative_to(root)),
                               **parquet_summary(data_parquet)}
    ep_parquet = next((root / "meta" / "episodes").rglob("*.parquet"), None)
    if ep_parquet is not None:
        out["episodes_parquet"] = {"path": str(ep_parquet.relative_to(root)),
                                   **parquet_summary(ep_parquet)}
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.stat().st_size > 0:
            out["files_listed"].append(str(f.relative_to(root)))
        if len(out["files_listed"]) >= 20:
            break
    return out


def online_inspect() -> dict:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset  # type: ignore

    ds = LeRobotDataset(repo_id=REPO_ID)
    sample = ds[0]
    feat_summary = {}
    for k, v in sample.items():
        if hasattr(v, "shape"):
            feat_summary[k] = {"shape": list(v.shape), "dtype": str(v.dtype)}
        elif isinstance(v, (int, float, str, bool)):
            feat_summary[k] = {"value": str(v)[:80]}
        else:
            feat_summary[k] = {"type": type(v).__name__}
    return {
        "repo_id": REPO_ID,
        "status": "online_loaded",
        "num_episodes": int(getattr(ds.meta, "total_episodes", -1)),
        "num_frames": int(getattr(ds.meta, "total_frames", -1)),
        "fps": float(getattr(ds.meta, "fps", -1)),
        "feature_keys": list(getattr(ds.meta, "features", {}).keys()),
        "first_sample": feat_summary,
    }


def main() -> None:
    print(f"trying repo_id = {REPO_ID}")
    # Step 1: try the full loader.
    online_err = None
    try:
        summary = online_inspect()
        print(json.dumps(summary, indent=2, default=str))
        (OUT_DIR / "dataset_inspect.json").write_text(
            json.dumps(summary, indent=2, default=str)
        )
        print(f"wrote {OUT_DIR / 'dataset_inspect.json'}")
        return
    except Exception as exc:  # noqa: BLE001
        online_err = repr(exc)
        print(f"online loader failed: {online_err}")
        print("falling back to offline parquet/json inspection...\n")

    # Step 2: try offline inspection.
    summary = offline_inspect()
    if summary is not None:
        summary["online_error"] = online_err
        print(json.dumps(summary, indent=2, default=str))
        (OUT_DIR / "dataset_inspect.json").write_text(
            json.dumps(summary, indent=2, default=str)
        )
        print(f"wrote {OUT_DIR / 'dataset_inspect.json'}")
        return

    # Step 3: cold path — nothing on disk, nothing online.
    err = {"repo_id": REPO_ID, "status": "skipped",
           "online_error": online_err,
           "offline_error": "no cached files at "
                            f"{CACHE_ROOT / REPO_ID}"}
    print(documented_layout())
    sk = OUT_DIR / "dataset_inspect.skipped"
    sk.write_text(json.dumps(err, indent=2) + "\n\n" + documented_layout())
    print(f"wrote {sk}")
    sys.exit(0)


if __name__ == "__main__":
    main()
