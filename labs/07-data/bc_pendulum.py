"""7.5 - Behavior cloning on the scripted pendulum dataset.

Reads ``runs/07-data/scripted_demos.npz`` produced by
``scripted_pendulum_demos.py``, trains an MLP policy ``obs -> action`` with
PyTorch, then closes the loop by rolling the policy out for 20 fresh targets.
Reports train loss, val loss and closed-loop final-error.

We keep the model tiny (≤120 lines, hidden=64, MLP-2) because the goal is to
expose covariate shift, not chase SOTA.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/07-data/bc_pendulum.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

DT = 0.005
TFINAL = 3.0
GRAVITY = 9.81
MASS = 1.0
LENGTH = 0.5
DAMPING = 0.10
TAU_LIMIT = 3.0


def pendulum_step(theta: float, omega: float, tau: float) -> tuple[float, float]:
    moi = MASS * LENGTH * LENGTH
    grav = -MASS * GRAVITY * LENGTH * math.sin(theta)
    omega_next = omega + DT * (tau + grav - DAMPING * omega) / moi
    theta_next = theta + DT * omega_next
    return theta_next, omega_next


class MLP(nn.Module):
    def __init__(self, in_dim: int = 3, out_dim: int = 1, hidden: int = 64) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def train(model: nn.Module, x: torch.Tensor, y: torch.Tensor, val_split: float = 0.2,
          batch: int = 256, epochs: int = 60, lr: float = 1e-3) -> dict:
    n = x.shape[0]
    perm = torch.randperm(n, generator=torch.Generator().manual_seed(0))
    x, y = x[perm], y[perm]
    n_val = int(n * val_split)
    x_tr, y_tr = x[n_val:], y[n_val:]
    x_va, y_va = x[:n_val], y[:n_val]

    opt = torch.optim.Adam(model.parameters(), lr=lr)
    train_curve, val_curve = [], []
    for ep in range(epochs):
        model.train()
        ids = torch.randperm(len(x_tr))
        losses = []
        for i in range(0, len(x_tr), batch):
            idx = ids[i:i+batch]
            pred = model(x_tr[idx])
            loss = ((pred - y_tr[idx]) ** 2).mean()
            opt.zero_grad(); loss.backward(); opt.step()
            losses.append(loss.item())
        model.eval()
        with torch.no_grad():
            val = ((model(x_va) - y_va) ** 2).mean().item()
        train_curve.append(float(np.mean(losses)))
        val_curve.append(val)
    return {"train_mse": train_curve, "val_mse": val_curve}


def closed_loop(model: nn.Module, target: float, theta0: float = 0.0,
                omega0: float = 0.0) -> dict:
    n = int(TFINAL / DT)
    theta, omega = theta0, omega0
    err_traj = []
    for _ in range(n):
        obs = torch.tensor([[theta, omega, target]], dtype=torch.float32)
        with torch.no_grad():
            tau = float(model(obs).item())
        tau = float(np.clip(tau, -TAU_LIMIT, TAU_LIMIT))
        theta, omega = pendulum_step(theta, omega, tau)
        err_traj.append(target - theta)
    return {"final_err": err_traj[-1], "max_err": max(abs(e) for e in err_traj)}


def main() -> None:
    torch.manual_seed(0)
    data = np.load("runs/07-data/scripted_demos.npz")
    x = torch.tensor(data["obs"], dtype=torch.float32)
    y = torch.tensor(data["act"], dtype=torch.float32)

    model = MLP()
    n_params = sum(p.numel() for p in model.parameters())
    history = train(model, x, y)

    rng = np.random.default_rng(123)
    eval_targets = rng.uniform(-math.radians(80), math.radians(80), size=20)
    finals = []
    for tgt in eval_targets:
        finals.append(closed_loop(model, float(tgt)))
    finals_deg = [abs(math.degrees(f["final_err"])) for f in finals]

    metrics = {
        "n_params": n_params,
        "n_train": int(0.8 * len(x)),
        "n_val": int(0.2 * len(x)),
        "train_mse_final": history["train_mse"][-1],
        "val_mse_final": history["val_mse"][-1],
        "closed_loop_final_err_deg_mean": float(np.mean(finals_deg)),
        "closed_loop_final_err_deg_median": float(np.median(finals_deg)),
        "closed_loop_final_err_deg_p95": float(np.percentile(finals_deg, 95)),
        "closed_loop_success_rate@2deg": float(np.mean([f < 2.0 for f in finals_deg])),
        "closed_loop_success_rate@5deg": float(np.mean([f < 5.0 for f in finals_deg])),
    }

    out = Path("runs/07-data/bc_metrics.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2))

    print(f"params           : {n_params}")
    print(f"final train MSE  : {history['train_mse'][-1]:.4e}")
    print(f"final val   MSE  : {history['val_mse'][-1]:.4e}")
    print(f"closed-loop |err| deg  mean={metrics['closed_loop_final_err_deg_mean']:.2f}"
          f"  median={metrics['closed_loop_final_err_deg_median']:.2f}"
          f"  p95={metrics['closed_loop_final_err_deg_p95']:.2f}")
    print(f"success@2deg     : {metrics['closed_loop_success_rate@2deg']:.0%}")
    print(f"success@5deg     : {metrics['closed_loop_success_rate@5deg']:.0%}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
