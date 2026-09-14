"""11.7 — Smoke tests for the chapter-03 labs.

What 'smoke' means here:
- runs the existing lab scripts under the same python that CI would use,
- captures their stdout,
- asserts the simplest invariant per lab (round-trip error < 1e-12,
  exit code 0, non-empty trace).

Designed to be cheap (<5 s total on CPU) so it can sit in every PR check.
Exit code 0 on success, 1 on any failure.

Run:
    python labs/11-eval/smoke_test_runner.py

Outputs:
    runs/11-eval/smoke_test_report.json
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable
ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def check_se3() -> dict:
    rc, out, err = run([PYTHON, "labs/03-robotics/se3_transforms.py"])
    m = re.search(r"round-trip error\s*=\s*([0-9eE.+\-]+)", out)
    err_val = float(m.group(1)) if m else float("inf")
    ok = (rc == 0) and (err_val < 1e-12)
    return {"name": "se3_transforms", "rc": rc, "round_trip_err": err_val,
            "threshold": 1e-12, "ok": ok, "stderr_tail": err[-200:] if err else ""}


def check_fk_ik() -> dict:
    rc, out, err = run([PYTHON, "labs/03-robotics/two_link_fk_ik.py"])
    m = re.search(r"targets evaluated:\s*(\d+),\s*successes:\s*(\d+)", out)
    total = int(m.group(1)) if m else 0
    succ = int(m.group(2)) if m else 0
    ok = (rc == 0) and total > 0 and succ > 0
    return {"name": "two_link_fk_ik", "rc": rc, "targets": total, "successes": succ,
            "ok": ok, "stderr_tail": err[-200:] if err else ""}


def check_pd() -> dict:
    rc, out, err = run([PYTHON, "labs/03-robotics/pd_control.py"])
    csv_path = ROOT / "runs/03-robotics/pd_curve.csv"
    has_csv = csv_path.exists() and csv_path.stat().st_size > 0
    ok = (rc == 0) and has_csv and "kp" in out
    return {"name": "pd_control", "rc": rc, "csv_exists": has_csv,
            "csv_size_bytes": (csv_path.stat().st_size if has_csv else 0),
            "ok": ok, "stderr_tail": err[-200:] if err else ""}


def main() -> int:
    import argparse
    import os
    import tempfile

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(ROOT / "runs/11-eval/smoke_test_report.json"),
        help="Where to write the JSON report (default: runs/11-eval/smoke_test_report.json)",
    )
    args = parser.parse_args()

    results = [check_se3(), check_fk_ik(), check_pd()]
    out_path = Path(args.output)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        all_ok = all(r["ok"] for r in results)
        report = {"all_ok": all_ok, "results": results}
        out_path.write_text(json.dumps(report, indent=2) + "\n")
    except OSError:
        # Read-only filesystem (e.g. CI sandbox). Fall back to $TMPDIR/tmp.
        fallback = Path(os.environ.get("TMPDIR", tempfile.gettempdir())) / out_path.name
        all_ok = all(r["ok"] for r in results)
        report = {"all_ok": all_ok, "results": results, "fallback_path": str(fallback)}
        fallback.write_text(json.dumps(report, indent=2) + "\n")
        out_path = fallback

    print(f"{'check':>20}  {'rc':>3}  {'ok':>3}  detail")
    for r in results:
        detail_keys = [k for k in r if k not in ("name", "rc", "ok", "stderr_tail")]
        detail = " ".join(f"{k}={r[k]}" for k in detail_keys)
        print(f"{r['name']:>20}  {r['rc']:>3}  {('Y' if r['ok'] else 'N'):>3}  {detail}")
    print(f"\nwrote {out_path}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
