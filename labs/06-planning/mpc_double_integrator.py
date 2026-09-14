"""6.4 — Finite-horizon MPC on a double integrator.

System: a point mass tracking a reference trajectory in 1D.
    x_{k+1} = A x_k + B u_k
    x = [position, velocity], u = acceleration
    A = [[1, dt], [0, 1]], B = [[0.5 dt^2], [dt]]

Reference: a smooth sinusoid plus a step change at ``t = 5 s``.

Two controllers are compared:

* LQR — solves the infinite-horizon DARE once, then applies ``u = -K x``.
  This is the textbook baseline and runs in microseconds per step.
* MPC — at each step, solves a finite-horizon QP via closed-form
  least-squares with input bounds enforced by clamping.  We use horizon
  ``N = 20``.  The QP is set up by stacking the dynamics into a single
  predict-then-track equation; for the unconstrained part we just
  invert the resulting block-matrix system.

Run:
    python labs/06-planning/mpc_double_integrator.py
"""
from __future__ import annotations

import math
import os

import numpy as np
from numpy.linalg import solve


RUN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs", "06-planning"))
os.makedirs(RUN_DIR, exist_ok=True)


dt = 0.05
N_SIM = 200   # 10 seconds
N_HOR = 20
U_MAX = 4.0

A = np.array([[1.0, dt], [0.0, 1.0]])
B = np.array([[0.5 * dt * dt], [dt]])

Q = np.diag([20.0, 1.0])
R = np.array([[0.05]])
QF = np.diag([100.0, 5.0])


def reference(t: float) -> np.ndarray:
    """Reference trajectory: sinusoid + step at t = 5 s."""
    pos = 0.5 * math.sin(0.8 * t)
    vel = 0.5 * 0.8 * math.cos(0.8 * t)
    if t > 5.0:
        pos += 1.0  # step
    return np.array([pos, vel])


# ---------------------------------------------------------------------------
# LQR via Discrete Algebraic Riccati Equation (iteration).
# ---------------------------------------------------------------------------
def dare(A, B, Q, R, max_iter=500, tol=1e-10):
    P = Q.copy()
    for _ in range(max_iter):
        K = solve(R + B.T @ P @ B, B.T @ P @ A)
        P_new = Q + A.T @ P @ (A - B @ K)
        if np.max(np.abs(P_new - P)) < tol:
            P = P_new
            break
        P = P_new
    K = solve(R + B.T @ P @ B, B.T @ P @ A)
    return P, K


# ---------------------------------------------------------------------------
# MPC: build prediction matrices Phi, Psi so X = Phi x0 + Psi U.
# ---------------------------------------------------------------------------
def build_mpc_matrices():
    nx, nu = A.shape[0], B.shape[1]
    Phi = np.zeros((N_HOR * nx, nx))
    Psi = np.zeros((N_HOR * nx, N_HOR * nu))
    A_pow = np.eye(nx)
    for i in range(N_HOR):
        A_pow = A_pow @ A
        Phi[i * nx:(i + 1) * nx, :] = A_pow
    for i in range(N_HOR):
        for j in range(i + 1):
            block = np.linalg.matrix_power(A, i - j) @ B
            Psi[i * nx:(i + 1) * nx, j * nu:(j + 1) * nu] = block
    # Stacked weights.
    Q_bar_diag = [Q] * (N_HOR - 1) + [QF]
    Q_bar = np.kron(np.eye(N_HOR), Q)
    for i in range(N_HOR):
        Q_bar[i * nx:(i + 1) * nx, i * nx:(i + 1) * nx] = Q_bar_diag[i]
    R_bar = np.kron(np.eye(N_HOR), R)
    H = Psi.T @ Q_bar @ Psi + R_bar
    return Phi, Psi, Q_bar, R_bar, H


def mpc_step(x, ref_future, Phi, Psi, Q_bar, H):
    f = Psi.T @ Q_bar @ (Phi @ x - ref_future)
    U = solve(H, -f)
    u0 = float(U[0])
    return max(-U_MAX, min(U_MAX, u0))


def main():
    P, K_lqr = dare(A, B, Q, R)
    print(f"LQR gain K = {K_lqr.flatten()}")

    Phi, Psi, Q_bar, R_bar, H = build_mpc_matrices()
    print(f"MPC horizon = {N_HOR}, prediction matrix shapes: Phi {Phi.shape}, Psi {Psi.shape}")

    x_lqr = np.array([0.5, 0.0])
    x_mpc = np.array([0.5, 0.0])
    log_lqr = []
    log_mpc = []

    for k in range(N_SIM):
        t = k * dt
        ref = reference(t)
        u_lqr = float((-K_lqr @ (x_lqr - ref)).item())
        u_lqr = max(-U_MAX, min(U_MAX, u_lqr))
        x_lqr = A @ x_lqr + (B @ np.array([u_lqr])).flatten()
        log_lqr.append((t, x_lqr[0], x_lqr[1], u_lqr, ref[0]))

        # MPC: build the stacked reference for the horizon.
        ref_future = np.zeros(N_HOR * 2)
        for i in range(N_HOR):
            ref_future[i * 2:(i + 1) * 2] = reference(t + (i + 1) * dt)
        u_mpc = mpc_step(x_mpc, ref_future, Phi, Psi, Q_bar, H)
        x_mpc = A @ x_mpc + (B @ np.array([u_mpc])).flatten()
        log_mpc.append((t, x_mpc[0], x_mpc[1], u_mpc, ref[0]))

    log_lqr = np.array(log_lqr)
    log_mpc = np.array(log_mpc)

    pos_err_lqr = np.sqrt(np.mean((log_lqr[:, 1] - log_lqr[:, 4]) ** 2))
    pos_err_mpc = np.sqrt(np.mean((log_mpc[:, 1] - log_mpc[:, 4]) ** 2))
    print(f"\nposition RMS error  LQR = {pos_err_lqr:.4f} m, MPC = {pos_err_mpc:.4f} m")
    print(f"final position      LQR = {log_lqr[-1, 1]:.4f} m, MPC = {log_mpc[-1, 1]:.4f} m, ref = {log_lqr[-1, 4]:.4f}")
    print(f"max |u|             LQR = {np.max(np.abs(log_lqr[:, 3])):.3f}, MPC = {np.max(np.abs(log_mpc[:, 3])):.3f} (limit {U_MAX})")

    # Pick out a few steps to print.
    print("\nstep    t      ref       x_lqr    u_lqr     x_mpc    u_mpc")
    for k in (0, 20, 50, 99, 100, 120, 150, 199):
        t = k * dt
        print(
            f"{k:4d} {t:5.2f} {log_lqr[k, 4]:8.4f}  {log_lqr[k, 1]:7.4f} {log_lqr[k, 3]:7.3f}  {log_mpc[k, 1]:7.4f} {log_mpc[k, 3]:7.3f}"
        )

    csv_path = os.path.join(RUN_DIR, "mpc_double_integrator.csv")
    with open(csv_path, "w") as f:
        f.write("t,ref_pos,x_lqr_pos,x_lqr_vel,u_lqr,x_mpc_pos,x_mpc_vel,u_mpc\n")
        for k in range(N_SIM):
            f.write(
                f"{log_lqr[k,0]:.4f},{log_lqr[k,4]:.5f},{log_lqr[k,1]:.5f},{log_lqr[k,2]:.5f},{log_lqr[k,3]:.5f},{log_mpc[k,1]:.5f},{log_mpc[k,2]:.5f},{log_mpc[k,3]:.5f}\n"
            )
    print(f"\nwrote {csv_path}")
    assert pos_err_mpc < 0.30, "MPC tracking error too large"
    assert pos_err_lqr < 0.50, "LQR tracking error too large"
    print(">>> PASS: both controllers track sinusoid+step within tolerance with bounded input.")


if __name__ == "__main__":
    main()
