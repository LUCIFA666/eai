"""11.5 — Minimal Hydra-style config composition (no Hydra dependency).

Demonstrates the *idea* behind Hydra / OmegaConf: a base YAML config,
a group of swappable variants (env, policy), and command-line overrides
(``key=value``).  Real projects should use the ``hydra-core`` package;
this script is a 60-line readable skeleton so learners can map every
piece to the corresponding Hydra concept:

- ``defaults:`` list                -> ``DEFAULTS`` dict below
- ``env=...`` override on CLI       -> ``key=value`` argv parsing
- multirun ``-m env=a,b``           -> outer loop in ``main()``
- structured config dataclass       -> the ``Config`` dict

Deterministic.  Writes the resolved config and a small fake metrics
file per (env, seed) cell so learners see the tracked-experiment layout.

Run:
    python labs/11-eval/hydra_config_example.py env=cartpole policy=pd seed=0
    python labs/11-eval/hydra_config_example.py            # uses defaults

Outputs:
    runs/11-eval/tracked/<env>__<policy>__seed<seed>/config.yaml
    runs/11-eval/tracked/<env>__<policy>__seed<seed>/metrics.json
    runs/11-eval/hydra_config_example.txt   (printed log)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

BASE_DIR = Path("runs/11-eval/tracked")

DEFAULTS = {"env": "cartpole", "policy": "pd", "seed": 0, "n_episodes": 5}

ENV_CONFIGS = {
    "cartpole": {"name": "CartPole-v1", "max_steps": 200, "obs_dim": 4, "act_dim": 2},
    "pendulum": {"name": "Pendulum-v1", "max_steps": 200, "obs_dim": 3, "act_dim": 1},
}

POLICY_CONFIGS = {
    "pd": {"kind": "PD", "kp": 15.0, "kd": 0.6, "params_count": 2},
    "random": {"kind": "Random", "noise": 1.0, "params_count": 0},
}


def parse_overrides(argv: list[str]) -> dict:
    overrides: dict[str, str | int | float] = {}
    for tok in argv:
        if "=" not in tok:
            continue
        k, v = tok.split("=", 1)
        try:
            overrides[k] = int(v)
        except ValueError:
            try:
                overrides[k] = float(v)
            except ValueError:
                overrides[k] = v
    return overrides


def compose(overrides: dict) -> dict:
    cfg = {**DEFAULTS, **overrides}
    if cfg["env"] not in ENV_CONFIGS:
        raise SystemExit(f"unknown env={cfg['env']} (have {list(ENV_CONFIGS)})")
    if cfg["policy"] not in POLICY_CONFIGS:
        raise SystemExit(f"unknown policy={cfg['policy']} (have {list(POLICY_CONFIGS)})")
    return {**cfg, "env_cfg": ENV_CONFIGS[cfg["env"]],
            "policy_cfg": POLICY_CONFIGS[cfg["policy"]]}


def fake_eval(cfg: dict) -> dict:
    # Deterministic synthetic metric tied to the config — proves the
    # config affected the result and was not silently dropped.
    s = int(cfg["seed"])
    base = 0.50 if cfg["policy"] == "random" else 0.85
    jitter = ((s * 7) % 11) * 0.01
    success = round(base + jitter - 0.05, 4)
    return {"success_rate": success, "episodes": int(cfg["n_episodes"]),
            "env": cfg["env_cfg"]["name"], "policy": cfg["policy_cfg"]["kind"]}


def main() -> None:
    overrides = parse_overrides(sys.argv[1:])
    cfg = compose(overrides)
    run_dir = BASE_DIR / f"{cfg['env']}__{cfg['policy']}__seed{cfg['seed']}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    metrics = fake_eval(cfg)
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"resolved config -> {run_dir / 'config.yaml'}")
    print(yaml.safe_dump(cfg, sort_keys=False), end="")
    print(f"metrics         -> {run_dir / 'metrics.json'}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
