"""9.4 — Static inspection of the local ``reference/openpi`` source tree.

We do NOT download any checkpoint here — that would pull tens of GB
from ``gs://openpi-assets/checkpoints/...``. Instead we walk the
config registry to list which named training configs ship in the
repo, and which checkpoints they point at.

This gives the learner a verified "menu" before they decide what to
download.

Run:
    python labs/09-vla/openpi_inspect.py

Outputs:
- prints a table of (name, model, weight_loader, ckpt_uri) tuples
- writes ``runs/09-vla/openpi_configs.json``
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path("reference/openpi")
CFG = REPO / "src/openpi/training/config.py"
OUT = Path("runs/09-vla/openpi_configs.json")


def main() -> None:
    if not CFG.exists():
        raise SystemExit(
            f"openpi config not found at {CFG}. Run `git submodule update` or "
            "clone https://github.com/Physical-Intelligence/openpi into reference/."
        )

    text = CFG.read_text()
    # The registry of configs is the list of TrainConfig(...) entries near the
    # bottom of config.py.  We don't import (no JAX needed) — we grep.
    # Each TrainConfig has at least `name="..."` and usually a `weight_loader`
    # field pointing at `weight_loaders.CheckpointWeightLoader("gs://...")`.
    name_re = re.compile(r'name=\s*"([a-zA-Z0-9_.\-]+)"')
    ckpt_re = re.compile(r'CheckpointWeightLoader\(\s*"([^"]+)"')

    # Walk the file by TrainConfig entries.  The official terminator for
    # each entry is `\n    )` at indent 4 (config.py is _CONFIGS = (...)).
    entries: list[dict] = []
    blocks = re.split(r"TrainConfig\(", text)
    for blk in blocks[1:]:
        # boundary = the first line that is exactly "    )," or "    )"
        m = re.search(r"\n    \)(,|\n)", blk)
        head = blk[: m.start()] if m else blk
        n = name_re.search(head)
        c = ckpt_re.search(head)
        if n is None:
            continue
        entries.append(
            {
                "name": n.group(1),
                "checkpoint": c.group(1)
                if c
                else "(no CheckpointWeightLoader — train from scratch)",
            }
        )

    # Dedup, keep first occurrence
    seen: set[str] = set()
    unique = []
    for e in entries:
        if e["name"] in seen:
            continue
        seen.add(e["name"])
        unique.append(e)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "source_file": str(CFG),
        "openpi_commit": _git_commit(REPO),
        "num_configs": len(unique),
        "configs": unique,
    }
    OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print(f"openpi commit: {summary['openpi_commit']}")
    print(f"found {len(unique)} TrainConfig entries in {CFG.name}\n")
    print(f"{'name':<32}  checkpoint")
    print("-" * 96)
    for e in unique:
        ck = e["checkpoint"]
        if len(ck) > 60:
            ck = ck[:57] + "..."
        print(f"{e['name']:<32}  {ck}")
    print(f"\nwrote {OUT}")
    print(
        "\n[note] To actually run inference you must download a checkpoint "
        "(~5-20 GB) and `uv pip install -e .` inside reference/openpi. See "
        "section/07-vlm-vla-and-foundation-models/03-common-libraries/09-openpi.md."
    )


def _git_commit(repo: Path) -> str:
    head = repo / ".git" / "HEAD"
    if not head.exists():
        # Could be a submodule with a redirected .git
        gitfile = repo / ".git"
        if gitfile.is_file():
            return gitfile.read_text().strip()
        return "(no .git)"
    ref = head.read_text().strip()
    if ref.startswith("ref:"):
        ref_path = repo / ".git" / ref.split(" ", 1)[1]
        if ref_path.exists():
            return ref_path.read_text().strip()[:12]
        return ref
    return ref[:12]


if __name__ == "__main__":
    main()
