"""4.7 — Fair speed benchmark: CPU (multiprocess) vs MJX (GPU batch).

Both sides run N parallel envs, so the "MJX vs CPU" ratio is apples-to-apples
(same parallelism, who's faster) rather than GPU-parallel vs one CPU env:
  - CPU: N envs spread across up to os.cpu_count() worker processes.
  - MJX: N envs via jax.vmap on the GPU.

Two correctness details that matter for a believable benchmark:
  1. CPU phase runs BEFORE jax is imported, so multiprocessing fork() does not
     collide with JAX's threads.
  2. Worker timing excludes one-time model loading; MJX side excludes
     put_model/JIT-compile via warmup.

Self-contained: uses an inline articulated-chain model (no menagerie needed).
Point MJX_MODEL_XML at a real scene.xml to benchmark a specific robot instead.

Two configs (same script):
  - Reader  (defaults): small batches, ~1 min on a modest GPU.
  - Verify: MJX_BATCH_SIZES=1,256,2048,8192 N_STEPS=100 CPU_MAX_N=2048 \
            python labs/04-simulation/mjx_speed_benchmark.py

REQUIRES: jax + mujoco-mjx. GPU recommended for the MJX side.

Run:
    python labs/04-simulation/mjx_speed_benchmark.py

Outputs:
    runs/04-simulation/mjx_speed_benchmark.txt
    runs/04-simulation/mjx_speed_benchmark.csv
"""
from __future__ import annotations

import csv
import os
import time
from pathlib import Path

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

import mujoco  # only mujoco at module top (NO jax) so the CPU fork phase is safe

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

BATCH_SIZES = [int(x) for x in
               os.environ.get("MJX_BATCH_SIZES", "1,16,256,1024,4096").split(",")]
N_STEPS = int(os.environ.get("N_STEPS", "200"))       # steps per measurement
WARMUP = int(os.environ.get("WARMUP", "20"))          # MJX warmup (amortize JIT)
CPU_MAX_N = int(os.environ.get("CPU_MAX_N", "1024"))  # CPU saturates at ~#cores
N_LINKS = int(os.environ.get("N_LINKS", "8"))         # inline model complexity
N_WORKERS = int(os.environ.get("CPU_WORKERS", str(os.cpu_count() or 4)))


def build_chain_xml(n_links: int) -> str:
    """Free-floating articulated chain of capsules on a floor: free base (6 DOF)
    + (n_links-1) hinges, with floor contact."""
    bodies, closing = "", ""
    for i in range(n_links):
        pos = "0 0 1.5" if i == 0 else "0.12 0 0"
        joint = "<freejoint/>" if i == 0 else f'<joint name="j{i}" type="hinge" axis="0 1 0"/>'
        bodies += (f'<body name="b{i}" pos="{pos}">{joint}'
                   f'<geom type="capsule" fromto="0 0 0 0.12 0 0" size="0.025"/>')
        closing += "</body>"
    acts = "".join(f'<motor joint="j{i}" ctrlrange="-1 1"/>' for i in range(1, n_links))
    return (f'<mujoco><option timestep="0.004"/><worldbody>'
            f'<geom type="plane" size="5 5 0.1"/>{bodies}{closing}'
            f'</worldbody><actuator>{acts}</actuator></mujoco>')


def get_model_xml() -> tuple[str, str]:
    path = os.environ.get("MJX_MODEL_XML")
    if path:
        return Path(path).read_text(), f"file:{Path(path).name}"
    return build_chain_xml(N_LINKS), f"inline_chain(n_links={N_LINKS})"


# ---------- CPU side: multiprocess, model-load excluded from timing ----------
def _cpu_worker(args):
    xml, n_envs, n_steps = args
    m = mujoco.MjModel.from_xml_string(xml)        # one-time, NOT timed
    t0 = time.perf_counter()
    for _ in range(n_envs):
        d = mujoco.MjData(m)
        for _ in range(n_steps):
            mujoco.mj_step(m, d)
    return n_envs * n_steps, time.perf_counter() - t0


def bench_cpu_parallel(xml: str, N: int, n_steps: int, n_workers: int) -> float:
    """N envs across min(N, n_workers) processes. Returns aggregate env-steps/s
    (bounded by the slowest worker, i.e. true parallel throughput)."""
    import multiprocessing as mp
    w = min(N, n_workers)
    base, rem = divmod(N, w)
    counts = [base + (1 if i < rem else 0) for i in range(w)]
    args = [(xml, c, n_steps) for c in counts if c > 0]
    if len(args) == 1:
        steps, elapsed = _cpu_worker(args[0])
        return steps / elapsed
    with mp.Pool(len(args)) as pool:
        res = pool.map(_cpu_worker, args)
    total = sum(s for s, _ in res)
    wall = max(e for _, e in res)
    return total / wall


def main():
    xml, label = get_model_xml()
    model = mujoco.MjModel.from_xml_string(xml)
    print(f"[info] model: {label}  nq={model.nq} nv={model.nv} nu={model.nu}")
    print(f"[info] CPU workers: {N_WORKERS}  steps/measure: {N_STEPS}")

    # ---- PHASE 1: CPU multiprocess (jax NOT imported yet -> fork is safe) ----
    cpu_sps, last = {}, None
    for N in BATCH_SIZES:
        if N <= CPU_MAX_N:
            last = bench_cpu_parallel(xml, N, N_STEPS, N_WORKERS)
            cpu_sps[N] = last
        else:
            cpu_sps[N] = last  # CPU saturates at ~#cores -> reuse plateau

    # ---- PHASE 2: MJX on GPU (import jax only now) ----
    import jax
    import jax.numpy as jnp
    from mujoco import mjx
    print(f"[info] JAX backend: {jax.default_backend()}  devices: {jax.devices()}\n")
    mjx_model = mjx.put_model(model)
    mjx_data = mjx.make_data(model)

    def bench_mjx(N: int, n_steps: int, warmup: int) -> float:
        @jax.jit
        def batch_step(bd):
            return jax.vmap(lambda d: mjx.step(mjx_model, d))(bd)
        bd = jax.tree_util.tree_map(
            lambda x: jnp.broadcast_to(x, (N,) + x.shape) if hasattr(x, "shape") else x,
            mjx_data)
        for _ in range(warmup):
            bd = batch_step(bd)
        bd.qpos.block_until_ready()
        t0 = time.perf_counter()
        for _ in range(n_steps):
            bd = batch_step(bd)
        bd.qpos.block_until_ready()
        return (N * n_steps) / (time.perf_counter() - t0)

    rows = [["N", "cpu_env_steps_per_s", "mjx_env_steps_per_s", "mjx_vs_cpu"]]
    for N in BATCH_SIZES:
        c = cpu_sps.get(N)
        c_str = ((f"{c:.0f}" if N <= CPU_MAX_N else f"~{c:.0f}(plateau)") if c else "n/a")
        try:
            m_sps = bench_mjx(N, N_STEPS, WARMUP)
            ratio = (m_sps / c) if c else float("nan")
            print(f"  N={N:>6d}  CPU={c_str:>16}  MJX={m_sps:>12.0f} env-steps/s  ({ratio:.2f}x vs CPU)")
            rows.append([N, c_str, f"{m_sps:.0f}", f"{ratio:.2f}"])
        except Exception as exc:
            print(f"  N={N:>6d}  MJX FAILED: {type(exc).__name__}: {exc!s}"[:110])
            rows.append([N, c_str, "FAILED", str(exc)[:60]])

    csv_path = RUNS / "mjx_speed_benchmark.csv"
    with open(csv_path, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    txt_path = RUNS / "mjx_speed_benchmark.txt"
    head = ("Fair benchmark - CPU(multiprocess) vs MJX(GPU vmap), both run N parallel envs\n"
            f"JAX backend: {jax.default_backend()}  devices: {[str(d) for d in jax.devices()]}\n"
            f"model: {label}  nq={model.nq} nv={model.nv} nu={model.nu}\n"
            f"CPU workers: {N_WORKERS}  steps/measure: {N_STEPS}\n\n"
            f"{'N':>7}  {'CPU env-steps/s':>18}  {'MJX env-steps/s':>16}  {'MJX/CPU':>8}\n"
            + "-" * 60 + "\n")
    body = "\n".join(f"{r[0]:>7}  {r[1]:>18}  {r[2]:>16}  {r[3]:>8}" for r in rows[1:])
    txt_path.write_text(head + body + "\n")
    print(f"\n[write] {csv_path}\n[write] {txt_path}")


if __name__ == "__main__":
    main()
