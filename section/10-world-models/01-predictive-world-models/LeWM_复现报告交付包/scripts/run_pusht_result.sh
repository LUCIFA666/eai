#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STABLEWM_HOME="${STABLEWM_HOME:-$HOME/.stable-wm}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export STABLEWM_HOME CUDA_VISIBLE_DEVICES

cd "$REPO_ROOT"

bash scripts/download_pusht.sh

"$REPO_ROOT/.venv/bin/python" - <<'PY'
import os
from pathlib import Path

import h5py
import hdf5plugin  # noqa: F401 -- registers the compression filters

path = Path(os.environ["STABLEWM_HOME"]) / "datasets" / "pusht_expert_train.h5"
with h5py.File(path, "r") as handle:
    required = {"pixels", "action", "proprio", "state", "ep_len", "ep_offset"}
    missing = required.difference(handle.keys())
    assert not missing, f"missing HDF5 keys: {sorted(missing)}"
    assert handle["ep_len"].shape[0] >= 1, "dataset has no episodes"
print(f"HDF5 verification passed: {path}")
PY

"$REPO_ROOT/.venv/bin/python" eval.py --config-name=pusht.yaml \
  policy=pusht/lewm \
  eval.num_eval=1 \
  eval.eval_budget=25 \
  solver.num_samples=30 \
  solver.n_steps=2 \
  output.filename=pusht_real_smoke_results.txt
