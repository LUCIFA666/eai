#!/usr/bin/env bash
set -euo pipefail

STABLEWM_HOME="${STABLEWM_HOME:-$HOME/.stable-wm}"
ARCHIVE="$STABLEWM_HOME/downloads/pusht_expert_train.h5.zst"
TOTAL_BYTES=13136247974
LOG_PATH="${1:-artifacts/real_result/progress.log}"

mkdir -p "$(dirname "$LOG_PATH")"
while tmux has-session -t lewm-pusht 2>/dev/null; do
  if [[ -f "$ARCHIVE" ]]; then
    current_bytes=$(stat -c '%s' "$ARCHIVE")
    percent=$(awk -v n="$current_bytes" -v d="$TOTAL_BYTES" 'BEGIN {printf "%.2f", 100*n/d}')
    printf '%s archive=%s bytes progress=%s%%\n' \
      "$(date --iso-8601=seconds)" "$current_bytes" "$percent" >> "$LOG_PATH"
  else
    printf '%s archive=not-created\n' "$(date --iso-8601=seconds)" >> "$LOG_PATH"
  fi
  sleep 600
done

printf '%s pipeline-session-ended\n' "$(date --iso-8601=seconds)" >> "$LOG_PATH"
