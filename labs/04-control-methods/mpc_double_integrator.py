"""Constrained receding-horizon MPC demo for section 4.3.1.

The plant is a one-dimensional double integrator.  At every control tick we
optimize a bounded acceleration sequence, apply only the first action, measure
the new state, shift the previous solution, and solve again.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize


def dynamics_matrices(dt: float) -> tuple[np.ndarray, np.ndarray]:
    a = np.array([[1.0, dt], [0.0, 1.0]])
    b = np.array([[0.5 * dt**2], [dt]])
    return a, b


def rollout(x0: np.ndarray, controls: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    states = [x0.copy()]
    state = x0.copy()
    for control in controls:
        state = a @ state + b[:, 0] * control
        states.append(state.copy())
    return np.asarray(states)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--horizon", type=int, default=24)
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--max-acceleration", type=float, default=1.2)
    parser.add_argument("--target", type=float, default=1.5)
    parser.add_argument("--output", type=Path, default=Path("mpc_double_integrator.png"))
    args = parser.parse_args()
    if args.dt <= 0.0 or args.horizon < 2 or args.steps < 2 or args.max_acceleration <= 0.0:
        raise ValueError("dt, max acceleration and sizes must be positive")

    a, b = dynamics_matrices(args.dt)
    target = np.array([args.target, 0.0])
    q = np.diag([9.0, 0.8])
    q_terminal = np.diag([25.0, 3.0])
    r = 0.12
    bounds = [(-args.max_acceleration, args.max_acceleration)] * args.horizon

    state = np.array([0.0, 0.0])
    warm_start = np.zeros(args.horizon)
    state_log = [state.copy()]
    control_log: list[float] = []
    solve_ms: list[float] = []
    status_log: list[bool] = []
    first_prediction: np.ndarray | None = None
    disturbance_step = args.steps // 2

    def objective(controls: np.ndarray, initial_state: np.ndarray) -> float:
        predicted = rollout(initial_state, controls, a, b)
        error = predicted[:-1] - target
        terminal_error = predicted[-1] - target
        running_cost = np.einsum("bi,ij,bj->", error, q, error)
        return float(running_cost + r * controls @ controls + terminal_error @ q_terminal @ terminal_error)

    for step in range(args.steps):
        started = perf_counter()
        result = minimize(
            objective,
            warm_start,
            args=(state.copy(),),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 80, "ftol": 1e-9},
        )
        solve_ms.append((perf_counter() - started) * 1000.0)
        status_log.append(bool(result.success))
        controls = np.asarray(result.x)
        prediction = rollout(state, controls, a, b)
        if first_prediction is None:
            first_prediction = prediction

        control = float(controls[0])
        state = a @ state + b[:, 0] * control
        if step == disturbance_step:
            state[1] -= 0.8  # reproducible velocity impulse

        control_log.append(control)
        state_log.append(state.copy())
        warm_start = np.r_[controls[1:], controls[-1]]

    states = np.asarray(state_log)
    controls = np.asarray(control_log)
    time = np.arange(args.steps + 1) * args.dt
    control_time = time[:-1]
    solve_ms_array = np.asarray(solve_ms)
    saturation = np.mean(np.isclose(np.abs(controls), args.max_acceleration, atol=1e-3))

    print(f"successful_solves={sum(status_log)}/{len(status_log)}")
    print(f"median_solve_ms={np.median(solve_ms_array):.3f}")
    print(f"p95_solve_ms={np.percentile(solve_ms_array, 95):.3f}")
    print(f"control_saturation_fraction={saturation:.3f}")
    print(f"final_state={states[-1]}")

    fig, axes = plt.subplots(4, 1, figsize=(9.5, 10.0), sharex=False, constrained_layout=True)
    axes[0].plot(time, states[:, 0], color="#0b6e69", label="position")
    axes[0].axhline(target[0], color="#ef8354", linestyle="--", label="target")
    if first_prediction is not None:
        prediction_time = np.arange(args.horizon + 1) * args.dt
        axes[0].plot(prediction_time, first_prediction[:, 0], color="#7a8793", linestyle=":", label="first prediction")
    axes[0].axvline(disturbance_step * args.dt, color="#75549a", linestyle=":", label="disturbance")
    axes[0].set_ylabel("position [m]")
    axes[0].legend(ncol=4, fontsize=8)

    axes[1].plot(time, states[:, 1], color="#247ba0")
    axes[1].axvline(disturbance_step * args.dt, color="#75549a", linestyle=":")
    axes[1].set_ylabel("velocity [m/s]")

    axes[2].step(control_time, controls, where="post", color="#f08a4b")
    axes[2].axhline(args.max_acceleration, color="#9aa8a3", linewidth=0.8)
    axes[2].axhline(-args.max_acceleration, color="#9aa8a3", linewidth=0.8)
    axes[2].set_ylabel("acceleration [m/s²]")

    axes[3].plot(control_time, solve_ms_array, color="#75549a")
    axes[3].axhline(args.dt * 1000.0, color="#c43f2d", linestyle="--", label="control period")
    axes[3].set(xlabel="time [s]", ylabel="solve time [ms]")
    axes[3].legend()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=170)
    print(f"saved={args.output.resolve()}")


if __name__ == "__main__":
    main()
