"""12.5 — Fill the model card template from a checkpoint metadata file.

Reads a JSON metadata sidecar (writes a synthetic one if missing) and
substitutes the values into ``labs/12-safety/model_card_template.md``.

Run:
    python labs/12-safety/generate_model_card.py
    python labs/12-safety/generate_model_card.py --ckpt-meta path/to/meta.json
Outputs:
    runs/12-safety/fake_ckpt.json    (synthetic input, only if missing)
    runs/12-safety/model_card.md     (rendered card)
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TEMPLATE = Path("labs/12-safety/model_card_template.md")
DEFAULT_META = Path("runs/12-safety/fake_ckpt.json")
DEFAULT_OUT = Path("runs/12-safety/model_card.md")

SYNTHETIC_META = {
    "model_id": "pickplace-bc-v0",
    "model_name": "PickPlace-BC-v0",
    "version": "v0.1",
    "train_step": 25000,
    "task": "tabletop_pickplace_block",
    "architecture": "ResNet18 -> MLP head",
    "n_params_m": 12.3,
    "input_modalities": "RGB 224x224 + joint_pos (7) + gripper_state (1)",
    "action_space": "delta_xyz (3) + delta_rpy (3) + gripper (1), normalised [-1,1]",
    "control_hz": 20,
    "license": "Apache-2.0",
    "dataset_name": "lab_pickplace_v0",
    "dataset_version": "2026-05-10",
    "n_train_episodes": 240,
    "n_val_episodes": 30,
    "train_envs": "MuJoCo tabletop (simulated)",
    "eval_suite": "tabletop_pickplace_eval_v0",
    "metric_name": "success_rate",
    "metric_value": 0.78,
    "metric_ci_lo": 0.71,
    "metric_ci_hi": 0.84,
    "n_eval_episodes": 50,
    "n_seeds": 3,
    "watchdog_ms": 200,
    "manifest_path": "runs/11-eval/manifest_example.json",
    "hardware": "1x NVIDIA RTX 4090",
    "seeds": [0, 1, 2],
    "eval_command": "python scripts/eval.py +ckpt=ckpts/pickplace-bc-v0/step25000.pt env=tabletop seeds=[0,1,2]",
    "citation_key": "pickplace_bc_v0_2026",
    "year": 2026,
}


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def _python_version() -> str:
    import sys
    return sys.version.split()[0]


def render(template: str, ctx: dict) -> str:
    # Lightweight {{key}} substitution; lists become comma-separated.
    out = template
    for k, v in ctx.items():
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v)
        out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt-meta", default=str(DEFAULT_META))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    a = p.parse_args()

    meta_path = Path(a.ckpt_meta)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    if not meta_path.exists():
        meta_path.write_text(json.dumps(SYNTHETIC_META, indent=2) + "\n")
        print(f"wrote synthetic checkpoint meta -> {meta_path}")
    meta = json.loads(meta_path.read_text())

    ctx = {**meta}
    ctx.setdefault("git_sha", _git_sha())
    ctx.setdefault("python_version", _python_version())
    ctx.setdefault("generated_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))

    template = TEMPLATE.read_text()
    rendered = render(template, ctx)

    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered)

    n_todo = rendered.count("TODO:")
    print(f"rendered model card -> {out_path}")
    print(f"  source meta: {meta_path}")
    print(f"  git SHA:     {ctx['git_sha'][:10]}")
    print(f"  metric:      {meta['metric_name']}={meta['metric_value']} "
          f"(CI {meta['metric_ci_lo']}-{meta['metric_ci_hi']}, n={meta['n_eval_episodes']})")
    print(f"  remaining TODO lines: {n_todo}")


if __name__ == "__main__":
    main()
