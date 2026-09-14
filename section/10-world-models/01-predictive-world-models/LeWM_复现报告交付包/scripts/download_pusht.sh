#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STABLEWM_HOME="${STABLEWM_HOME:-$HOME/.stable-wm}"
export STABLEWM_HOME

mkdir -p \
  "$STABLEWM_HOME/hf_pusht" \
  "$STABLEWM_HOME/downloads" \
  "$STABLEWM_HOME/datasets"
"$REPO_ROOT/.venv/bin/hf" download quentinll/lewm-pusht \
  config.json weights.pt --local-dir "$STABLEWM_HOME/hf_pusht"
if [[ ! -f "$STABLEWM_HOME/datasets/pusht_expert_train.h5" ]]; then
  # `hf download` may select Xet, whose TLS transport is blocked by some
  # proxies. curl uses the regular HTTPS resolve endpoint and `-C -` resumes
  # an interrupted archive at the existing byte offset.
  archive="$STABLEWM_HOME/downloads/pusht_expert_train.h5.zst"
  url="https://huggingface.co/datasets/quentinll/lewm-pusht/resolve/main/pusht_expert_train.h5.zst"
  until curl -fL -C - --retry 8 --retry-delay 3 -o "$archive" "$url"; do
    echo "Download interrupted; retrying the resumable transfer in 10 seconds..." >&2
    sleep 10
  done

  "$REPO_ROOT/.venv/bin/python" - <<'PY'
import os
from pathlib import Path

import zstandard as zstd

root = Path(os.environ["STABLEWM_HOME"])
source_path = root / "downloads" / "pusht_expert_train.h5.zst"
target_path = root / "datasets" / "pusht_expert_train.h5"
with source_path.open("rb") as source, target_path.open("wb") as target:
    zstd.ZstdDecompressor().copy_stream(source, target)
print(f"Decompressed dataset: {target_path}")
PY
fi

echo "Artifacts ready under $STABLEWM_HOME"
