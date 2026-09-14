#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

UV="${UV:-uv}"
if ! command -v "$UV" >/dev/null 2>&1; then
  echo "uv was not found. Install it from https://docs.astral.sh/uv/ first." >&2
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  "$UV" venv --python 3.10 .venv
fi

# box2d-py is built from source by gymnasium[all] and needs the SWIG binary.
"$UV" pip install --python .venv/bin/python swig==4.4.1
PATH="$REPO_ROOT/.venv/bin:$PATH" \
  "$UV" pip install --python .venv/bin/python -r requirements-repro.txt

echo "Environment ready: $REPO_ROOT/.venv"

