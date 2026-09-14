"""6.3 — iLQR swing-up on an under-actuated pendulum.

State ``x = [theta, theta_dot]`` (radians, radians/s).  Control ``u`` is
torque (Nm).  Dynamics::

    theta_ddot = -(g/L) sin(theta) - (b/m L^2) theta_dot + u / (m L^2)

We start at ``x0 = (pi, 0)`` (pointing down) and want to reach
``x_goal = (0, 0)`` (upright).  The peak torque is small enough that the
controller has to swing back-and-forth — the classic under-actuated
"swing-up" benchmark.

To dodge the discontinuity at theta = +/- pi we measure goal error in
**trigonometric coordinates** ``(1 - cos(theta), sin(theta), theta_dot)``
so the cost surface is smooth.  We then run a textbook iLQR with
analytic Jacobians of the discretised Euler dynamics.

Run:
    python labs/06-planning/ilqr_pendulum.py
"""
from __future__ import annotations

import math
import os

import numpy as np


RUN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs", "06-planning"))
os.makedirs(RUN_DIR, exist_ok=True)


# Physical parameters.
g, L, m, b = 9.81, 1.0, 1.0, 0.1
dt = 0.04
T = 200
U_MAX = 3.0

# Quadratic cost on (1 - cos(theta), sin(theta), theta_dot)
Q_DIAG = np.array([5.0, 1.0, 0.05])
QF_DIAG = np.array([500.0, 500.0, 50.0])
R_DIAG = np.array([0.05])


def wrap(angle):
    return ((angle + math.pi) % (2 * math.pi)) - math.pi


def dyn(x, u):
    th, dth = x
    u_val = float(u[0])
    ddth = -(g / L) * math.sin(th) - (b / (m * L * L)) * dth + u_val / (m * L * L)
    return np.array([th + dt * dth, dth + dt * ddth])


def dyn_jac(x, u):
    th, dth = x
    A = np.array([
        [1.0, dt],
        [-dt * (g / L) * math.cos(th), 1.0 - dt * (b / (m * L * L))],
    ])
    B = np.array([
        [0.0],
        [dt / (m * L * L)],
    ])
    return A, B


def smooth_residual(x):
    """Map ``(theta, theta_dot)`` to ``[1 - cos(theta), sin(theta), theta_dot]``.

    Upright corresponds to ``theta = 0`` ⇒ residual = ``(0, 0, 0)``.  At
    the bottom ``theta = pi`` ⇒ residual = ``(2, 0, 0)``.  Smooth
    everywhere.
    """
    th, dth = x
    return np.array([1.0 - math.cos(th), math.sin(th), dth])


def smooth_residual_jac(x):
    th, _ = x
    return np.array([
        [math.sin(th), 0.0],
        [math.cos(th), 0.0],
        [0.0, 1.0],
    ])


def cost(x, u, is_final=False):
    r = smooth_residual(x)
    diag = QF_DIAG if is_final else Q_DIAG
    j = float(np.sum(diag * r * r))
    if not is_final:
        j += float(np.sum(R_DIAG * u * u))
    return j


def cost_jacobians(x, u, is_final=False):
    r = smooth_residual(x)
    J_r = smooth_residual_jac(x)  # 3x2
    diag = QF_DIAG if is_final else Q_DIAG
    lx = 2.0 * J_r.T @ (diag * r)
    lxx = 2.0 * J_r.T @ np.diag(diag) @ J_r
    if is_final:
        return lx, lxx, np.zeros(1), np.zeros((1, 1)), np.zeros((1, 2))
    lu = 2.0 * R_DIAG * u
    luu = 2.0 * np.diag(R_DIAG)
    lux = np.zeros((1, 2))
    return lx, lxx, lu, luu, lux


def rollout(x0, U):
    xs = [x0.copy()]
    for u in U:
        xs.append(dyn(xs[-1], u))
    return np.array(xs)


def total_cost(xs, us):
    j = 0.0
    for t in range(T):
        j += cost(xs[t], us[t])
    j += cost(xs[T], np.zeros(1), is_final=True)
    return j


def ilqr(x0, U_init, n_iter=200):
    U = U_init.copy()
    xs = rollout(x0, U)
    J = total_cost(xs, U)
    log = [(0, J, 0.0, 1.0)]
    reg = 1e-3
    for it in range(1, n_iter):
        # Backward pass.
        lx_f, lxx_f, _, _, _ = cost_jacobians(xs[T], np.zeros(1), is_final=True)
        Vx = lx_f
        Vxx = lxx_f
        Ks = []
        ks = []
        for t in reversed(range(T)):
            A, B = dyn_jac(xs[t], U[t])
            lx, lxx, lu, luu, lux = cost_jacobians(xs[t], U[t])
            Qx = lx + A.T @ Vx
            Qu = lu + B.T @ Vx
            Qxx = lxx + A.T @ Vxx @ A
            Qux = lux + B.T @ Vxx @ A
            Quu = luu + B.T @ Vxx @ B + reg * np.eye(1)
            Quu_inv = np.linalg.inv(Quu)
            k = -Quu_inv @ Qu
            K = -Quu_inv @ Qux
            ks.append(k)
            Ks.append(K)
            Vx = Qx + K.T @ Quu @ k + K.T @ Qu + Qux.T @ k
            Vxx = Qxx + K.T @ Quu @ K + K.T @ Qux + Qux.T @ K
            Vxx = 0.5 * (Vxx + Vxx.T)
        Ks.reverse()
        ks.reverse()

        improved = False
        for alpha in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.01, 0.003):
            U_new = np.zeros_like(U)
            xs_new = [x0.copy()]
            for t in range(T):
                du = alpha * ks[t] + Ks[t] @ (xs_new[-1] - xs[t])
                U_new[t] = np.clip(U[t] + du, -U_MAX, U_MAX)
                xs_new.append(dyn(xs_new[-1], U_new[t]))
            xs_new = np.array(xs_new)
            J_new = total_cost(xs_new, U_new)
            if J_new < J - 1e-9:
                xs, U, J = xs_new, U_new, J_new
                improved = True
                reg = max(reg * 0.5, 1e-6)
                break
        log.append((it, J, reg, alpha))
        if not improved:
            reg = min(reg * 5.0, 1e8)
            if reg > 1e6:
                break
        if it >= 20 and abs(log[-20][1] - J) < 1e-5 * max(1.0, J):
            break
    return xs, U, J, log


def main():
    x0 = np.array([math.pi, 0.0])
    print(f"x0 = {x0}, T = {T}, dt = {dt}, u in [{-U_MAX}, {U_MAX}]")
    # Pumping warm start
    U_init = 0.8 * np.sin(np.linspace(0, 6 * math.pi, T)).reshape(-1, 1)
    xs, U, J, log = ilqr(x0, U_init)
    final_err_angle = math.degrees(abs(wrap(xs[-1, 0])))
    final_err_vel = abs(xs[-1, 1])
    print(f"\niLQR finished after {len(log)} iterations, final cost J = {J:.4f}")
    print(f"final state: theta = {xs[-1, 0]:.4f} rad ({final_err_angle:.2f} deg from upright), theta_dot = {xs[-1, 1]:.4f}")
    print(f"max torque applied = {np.max(np.abs(U)):.3f} Nm (limit {U_MAX})")
    print("\niLQR cost log (every 20 iters):")
    for it, j, r, a in log[::20]:
        print(f"  iter {it:03d}  cost = {j:10.4f}  reg = {r:.2e}  alpha = {a}")
    print(f"  iter {log[-1][0]:03d}  cost = {log[-1][1]:10.4f}  reg = {log[-1][2]:.2e}  alpha = {log[-1][3]}")

    with open(os.path.join(RUN_DIR, "ilqr_pendulum.csv"), "w") as f:
        f.write("t,theta,theta_dot,u\n")
        for t in range(T + 1):
            u = U[t][0] if t < T else 0.0
            f.write(f"{t*dt:.4f},{xs[t,0]:.5f},{xs[t,1]:.5f},{u:.5f}\n")
    print(f"\nwrote {os.path.join(RUN_DIR, 'ilqr_pendulum.csv')}")
    assert final_err_angle < 5.0 and final_err_vel < 0.5, (
        f"iLQR did not swing up; angle={final_err_angle:.2f} deg, vel={final_err_vel:.3f}"
    )
    print(">>> PASS: pendulum swings up to within 5 deg of upright with bounded torque.")


if __name__ == "__main__":
    main()
