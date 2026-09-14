"""4.7 — Minimal mujoco -> mjx migration (self-contained).

Shows the migration pattern and times JIT compile vs cached steps:
  - load a CPU model, mjx.put_model() it
  - single-env step:  data.replace(ctrl=...) -> mjx.step (pure, returns new data)
  - batched step via jax.vmap

Uses an inline model (no menagerie, fast compile, no OOM on small GPUs).
Point MJX_MODEL_XML at a real scene.xml to migrate a specific robot instead.

REQUIRES: jax + mujoco-mjx (GPU recommended).

Run:
    python labs/04-simulation/mjx_minimal.py

Outputs:
    runs/04-simulation/mjx_minimal.json   (timings + model summary)
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

import mujoco
from mujoco import mjx
import jax
import jax.numpy as jnp

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "04-simulation"
RUNS.mkdir(parents=True, exist_ok=True)

N_LINKS = int(os.environ.get("N_LINKS", "8"))
BATCH = int(os.environ.get("MJX_BATCH", "256"))


def build_chain_xml(n_links: int) -> str:
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


def get_model() -> tuple[mujoco.MjModel, str]:
    path = os.environ.get("MJX_MODEL_XML")
    if path:
        return mujoco.MjModel.from_xml_path(path), f"file:{Path(path).name}"
    return mujoco.MjModel.from_xml_string(build_chain_xml(N_LINKS)), f"inline_chain(n_links={N_LINKS})"


def main():
    print(f"[info] JAX backend: {jax.default_backend()}  devices: {jax.devices()}")
    model, label = get_model()
    print(f"[cpu] {label}  nq={model.nq} nv={model.nv} nu={model.nu}")

    # ---- move to MJX ----
    mjx_model = mjx.put_model(model)
    mjx_data = mjx.make_data(model)

    # ---- single-env step (pure function: returns new data) ----
    @jax.jit
    def step_one(data, ctrl):
        data = data.replace(ctrl=ctrl)
        return mjx.step(mjx_model, data)

    ctrl = jnp.zeros(model.nu)
    t0 = time.perf_counter()
    d = step_one(mjx_data, ctrl)          # first call: includes JIT compile
    d.qpos.block_until_ready()
    t_first = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(100):
        d = step_one(d, ctrl)             # cached: fast
    d.qpos.block_until_ready()
    t_step = (time.perf_counter() - t0) / 100
    print(f"[1-env] first call (JIT+step) = {t_first*1000:.1f} ms | "
          f"cached step = {t_step*1000:.3f} ms")

    # ---- batched step via vmap ----
    @jax.jit
    def step_batched(bd, bc):
        return jax.vmap(lambda da, c: mjx.step(mjx_model, da.replace(ctrl=c)))(bd, bc)

    batch_data = jax.tree_util.tree_map(
        lambda x: jnp.broadcast_to(x, (BATCH,) + x.shape) if hasattr(x, "shape") else x,
        mjx_data)
    batch_ctrl = jnp.zeros((BATCH, model.nu))
    t0 = time.perf_counter()
    out = step_batched(batch_data, batch_ctrl)
    out.qpos.block_until_ready()
    t_bfirst = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(50):
        out = step_batched(out, batch_ctrl)
    out.qpos.block_until_ready()
    t_bstep = (time.perf_counter() - t0) / 50
    print(f"[batch={BATCH}] first call (JIT+step) = {t_bfirst*1000:.1f} ms | "
          f"cached batch step = {t_bstep*1000:.3f} ms | "
          f"throughput = {BATCH/t_bstep:.0f} env-steps/s")

    info = {
        "jax_backend": jax.default_backend(),
        "jax_devices": [str(x) for x in jax.devices()],
        "model": label, "nq": int(model.nq), "nv": int(model.nv), "nu": int(model.nu),
        "single_first_step_ms": round(t_first * 1000, 3),
        "single_cached_step_ms": round(t_step * 1000, 3),
        "batch": BATCH,
        "batch_first_ms": round(t_bfirst * 1000, 3),
        "batch_cached_step_ms": round(t_bstep * 1000, 3),
        "batch_throughput_env_steps_per_s": round(BATCH / t_bstep, 1),
    }
    (RUNS / "mjx_minimal.json").write_text(json.dumps(info, indent=2))
    print(f"[write] {RUNS / 'mjx_minimal.json'}")


if __name__ == "__main__":
    main()
