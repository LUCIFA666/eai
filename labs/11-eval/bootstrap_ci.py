"""11.2 — Bootstrap confidence intervals for evaluation metrics.

Given a synthetic dataset of per-episode metrics (success {0,1}, return,
SPL, episode_length), compute:
- mean
- 95% bootstrap CI (percentile method)
- per-seed averages to expose between-seed variance

Deterministic with numpy seed=0. No scipy required.

Run:
    python labs/11-eval/bootstrap_ci.py

Outputs:
    runs/11-eval/bootstrap_ci.json    # numeric report
    runs/11-eval/bootstrap_ci.csv     # per-metric mean / lo / hi
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

N_SEEDS = 5
N_EPISODES_PER_SEED = 40
N_BOOTSTRAP = 2000
ALPHA = 0.05


def synth_dataset(rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Synthetic eval log: each row = (seed, success, return, spl, length)."""
    seeds = np.repeat(np.arange(N_SEEDS), N_EPISODES_PER_SEED)
    # Per-seed bias models between-run variance (e.g. different scene shuffles).
    bias = rng.normal(0.0, 0.04, size=N_SEEDS)[seeds]
    success_prob = np.clip(0.60 + bias, 0.0, 1.0)
    success = (rng.random(seeds.size) < success_prob).astype(np.int64)
    # Return: positive when successful, near zero when failed.
    ret = success * rng.normal(8.0, 1.2, seeds.size) + (1 - success) * rng.normal(-1.0, 0.5, seeds.size)
    # SPL only defined for successful runs; failures contribute 0.
    spl = success * np.clip(rng.normal(0.78, 0.10, seeds.size), 0.0, 1.0)
    length = np.clip(rng.normal(160, 40, seeds.size), 20, 500).astype(np.int64)
    return {"seed": seeds, "success": success, "return": ret, "spl": spl, "length": length}


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator,
                 n_boot: int = N_BOOTSTRAP, alpha: float = ALPHA) -> tuple[float, float, float]:
    n = values.size
    idx = rng.integers(0, n, size=(n_boot, n))
    boot_means = values[idx].mean(axis=1)
    lo = float(np.quantile(boot_means, alpha / 2))
    hi = float(np.quantile(boot_means, 1 - alpha / 2))
    return float(values.mean()), lo, hi


def per_seed_means(values: np.ndarray, seeds: np.ndarray) -> dict[int, float]:
    return {int(s): float(values[seeds == s].mean()) for s in np.unique(seeds)}


def main() -> None:
    rng = np.random.default_rng(0)
    ds = synth_dataset(rng)
    out_dir = Path("runs/11-eval"); out_dir.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {"config": {"n_seeds": N_SEEDS, "n_episodes_per_seed": N_EPISODES_PER_SEED,
                          "n_bootstrap": N_BOOTSTRAP, "alpha": ALPHA},
              "metrics": {}}
    rows = [("metric", "mean", "ci_lo", "ci_hi", "per_seed_min", "per_seed_max")]
    for name in ("success", "return", "spl", "length"):
        vals = ds[name].astype(np.float64)
        mean, lo, hi = bootstrap_ci(vals, rng)
        per_seed = per_seed_means(vals, ds["seed"])
        report["metrics"][name] = {"mean": mean, "ci95_lo": lo, "ci95_hi": hi,
                                    "per_seed": per_seed}
        rows.append((name, f"{mean:.4f}", f"{lo:.4f}", f"{hi:.4f}",
                     f"{min(per_seed.values()):.4f}", f"{max(per_seed.values()):.4f}"))

    (out_dir / "bootstrap_ci.json").write_text(json.dumps(report, indent=2) + "\n")
    with (out_dir / "bootstrap_ci.csv").open("w", newline="") as f:
        csv.writer(f).writerows(rows)

    print(f"dataset: {N_SEEDS} seeds x {N_EPISODES_PER_SEED} eps = {ds['success'].size} episodes")
    print(f"{'metric':>8}  {'mean':>8}  {'ci95_lo':>8}  {'ci95_hi':>8}  {'seed_min':>9}  {'seed_max':>9}")
    for r in rows[1:]:
        print(f"{r[0]:>8}  {r[1]:>8}  {r[2]:>8}  {r[3]:>8}  {r[4]:>9}  {r[5]:>9}")
    print(f"\nwrote {out_dir / 'bootstrap_ci.json'} and bootstrap_ci.csv")


if __name__ == "__main__":
    main()
