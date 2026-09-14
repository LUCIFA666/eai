"""Generate reproducible ManiSkill PickCube evidence for a tutorial page.

Run from the repository root:
    python labs/04-simulation/maniskill_pickcube_artifacts.py --steps 50

Suggested outputs:
    runs/04-simulation/maniskill_pickcube_summary.json
    runs/04-simulation/maniskill_pickcube_spaces.txt
    runs/04-simulation/maniskill_pickcube_reset.png
    runs/04-simulation/maniskill_pickcube_rollout.mp4
    runs/04-simulation/maniskill_pickcube_rgb.png
    runs/04-simulation/maniskill_pickcube_depth.png
    runs/04-simulation/maniskill_pickcube_vector.txt
    runs/04-simulation/maniskill_pickcube_wrapper.txt

The script is intentionally defensive: visual/GPU probes are skipped cleanly when
Vulkan/CUDA is not available, while the state-only smoke test remains the minimum
acceptance check.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import subprocess
import traceback
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = ROOT / "runs/04-simulation"


def _to_numpy(x: Any) -> np.ndarray:
    """Convert torch/numpy/list-like values to a CPU numpy array."""
    if hasattr(x, "detach"):
        x = x.detach()
    if hasattr(x, "cpu"):
        x = x.cpu()
    if hasattr(x, "numpy"):
        return x.numpy()
    return np.asarray(x)


def _jsonable(x: Any) -> Any:
    """Make common tensor/space outputs JSON serializable without losing shape info."""
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    if hasattr(x, "shape"):
        arr = _to_numpy(x)
        if arr.ndim == 0:
            return arr.item()
        if arr.size <= 12:
            return arr.tolist()
        return {"shape": list(arr.shape), "dtype": str(arr.dtype)}
    return str(x)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"[write] {path}")


# def _save_png(path: Path, frame: Any) -> None:
#     from PIL import Image
#
#     arr = _to_numpy(frame)
#     if arr.ndim == 4 and arr.shape[0] == 1:
#         arr = arr[0]
#     if arr.shape[-1] == 4:
#         arr = arr[..., :3]
#     if arr.dtype != np.uint8:
#         arr = np.clip(arr, 0, 255).astype(np.uint8)
#     Image.fromarray(arr).save(path)
#     print(f"[write] {path}")
def _save_png(path: Path, frame: Any, resize_to: tuple[int, int] | None = None) -> None:
    from PIL import Image

    arr = _to_numpy(frame)
    if arr.ndim == 4 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.shape[-1] == 4:
        arr = arr[..., :3]
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)

    img = Image.fromarray(arr)
    if resize_to is not None:
        img = img.resize(resize_to, Image.Resampling.BILINEAR)

    img.save(path)
    print(f"[write] {path}")


# def _save_depth_png(path: Path, depth: Any) -> None:
#     from PIL import Image
#
#     arr = _to_numpy(depth)
#     if arr.ndim == 4 and arr.shape[0] == 1:
#         arr = arr[0]
#     if arr.ndim == 3 and arr.shape[-1] == 1:
#         arr = arr[..., 0]
#     arr = arr.astype(np.float32)
#     valid = np.isfinite(arr) & (arr != 0)
#     if valid.any():
#         lo, hi = np.percentile(arr[valid], [2, 98])
#         if hi <= lo:
#             hi = lo + 1.0
#         arr = (arr - lo) / (hi - lo)
#     arr = np.clip(arr, 0, 1)
#     Image.fromarray((arr * 255).astype(np.uint8)).save(path)
#     print(f"[write] {path}")
def _save_depth_png(path: Path, depth: Any, resize_to: tuple[int, int] | None = None) -> None:
    from PIL import Image

    arr = _to_numpy(depth)
    if arr.ndim == 4 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.ndim == 3 and arr.shape[-1] == 1:
        arr = arr[..., 0]
    arr = arr.astype(np.float32)

    valid = np.isfinite(arr) & (arr != 0)
    if valid.any():
        lo, hi = np.percentile(arr[valid], [2, 98])
        if hi <= lo:
            hi = lo + 1.0
        arr = (arr - lo) / (hi - lo)

    arr = np.clip(arr, 0, 1)

    img = Image.fromarray((arr * 255).astype(np.uint8))
    if resize_to is not None:
        img = img.resize(resize_to, Image.Resampling.BILINEAR)

    img.save(path)
    print(f"[write] {path}")


def _render_frame(env: Any) -> Any:
    frame = env.render()
    if frame is None:
        raise RuntimeError("env.render() returned None; use render_mode='rgb_array'.")
    return frame


def _normalize_video_frame(frame: Any) -> np.ndarray:
    """Return a single H×W×3 uint8 frame for imageio video writing."""
    arr = _to_numpy(frame)
    # ManiSkill's batched interface may return (1, H, W, C) even for num_envs=1.
    if arr.ndim == 4 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.ndim != 3:
        raise ValueError(f"Expected an H×W×C frame after squeezing batch dim, got shape={arr.shape}")
    if arr.shape[-1] == 4:
        arr = arr[..., :3]
    if arr.shape[-1] != 3:
        raise ValueError(f"Expected RGB/RGBA frame, got shape={arr.shape}")
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr


def _save_video(path: Path, frames: list[Any], fps: int = 10) -> None:
    """Save MP4 if ffmpeg is available; otherwise save a GIF fallback and a skipped note."""
    import imageio.v2 as imageio

    path.parent.mkdir(parents=True, exist_ok=True)
    clean_frames = [_normalize_video_frame(f) for f in frames]
    try:
        imageio.mimsave(path, clean_frames, fps=fps, macro_block_size=1)
        print(f"[write] {path}")
    except Exception as exc:
        gif_path = path.with_suffix(".gif")
        imageio.mimsave(gif_path, clean_frames, fps=fps)
        note = (
            f"MP4 was not written because imageio/ffmpeg failed: {type(exc).__name__}: {exc}\n"
            "A GIF fallback was written. To enable MP4, run: pip install imageio-ffmpeg\n"
        )
        _write_text(path.with_suffix(path.suffix + ".skipped"), note)
        print(f"[write] {gif_path}")


def _space_report(env: Any) -> str:
    lines = [
        f"observation_space: {env.observation_space}",
        f"action_space: {env.action_space}",
    ]
    if hasattr(env, "single_observation_space"):
        lines.append(f"single_observation_space: {env.single_observation_space}")
    if hasattr(env, "single_action_space"):
        lines.append(f"single_action_space: {env.single_action_space}")
    return "\n".join(lines) + "\n"


def import_dependencies() -> tuple[Any, Any, Any]:
    try:
        import gymnasium as gym
        import mani_skill.envs  # noqa: F401  registers all ManiSkill environments
        import sapien
    except Exception as exc:  # keep broad; import can fail from missing Vulkan deps too
        msg = (
            "ManiSkill dependencies are not ready. Install and verify them first.\n"
            f"Error: {type(exc).__name__}: {exc}\n"
            "Suggested install: pip install --upgrade mani_skill torch imageio imageio-ffmpeg pillow\n"
        )
        raise RuntimeError(msg) from exc
    return gym, sys.modules["mani_skill.envs"], sapien


def probe_state_smoke(gym: Any, sapien: Any, out_dir: Path, steps: int) -> dict[str, Any]:
    env = gym.make(
        "PickCube-v1",
        num_envs=1,
        obs_mode="state",
        control_mode="pd_ee_delta_pose",
        render_mode="rgb_array",
    )
    summary: dict[str, Any] = {
        "task": "PickCube-v1",
        "obs_mode": "state",
        "control_mode": "pd_ee_delta_pose",
        "sapien_version": getattr(sapien, "__version__", "unknown"),
        "observation_space": str(env.observation_space),
        "action_space": str(env.action_space),
    }
    _write_text(out_dir / "maniskill_pickcube_spaces.txt", _space_report(env))

    obs, info = env.reset(seed=0)
    summary["reset_info_keys"] = sorted(list(info.keys()))
    summary["obs_after_reset"] = _jsonable(obs)
    _save_png(out_dir / "maniskill_pickcube_reset.png", _render_frame(env))

    rewards: list[float] = []
    success_values: list[Any] = []
    frames = []
    for i in range(steps):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        r_np = _to_numpy(reward).reshape(-1)
        rewards.append(float(r_np[0]))
        if "success" in info:
            success_values.append(_jsonable(info["success"]))
        if i % 2 == 0:  # keep the video small
            frames.append(_to_numpy(_render_frame(env)))
        done = np.asarray(_to_numpy(terminated) | _to_numpy(truncated)).any()
        if bool(done):
            break

    if frames:
        video_path = out_dir / "maniskill_pickcube_rollout.mp4"
        _save_video(video_path, frames, fps=10)
    else:
        _write_text(
            out_dir / "maniskill_pickcube_rollout.mp4.skipped",
            "No rollout frames were collected. Check --steps; it should be greater than 0.\n",
        )

    summary.update(
        {
            "n_steps": len(rewards),
            "mean_reward_random": float(np.mean(rewards)) if rewards else None,
            "max_reward_random": float(np.max(rewards)) if rewards else None,
            "last_success": success_values[-1] if success_values else None,
        }
    )
    env.close()
    return summary


def probe_rgbd(gym: Any, out_dir: Path) -> dict[str, Any]:
    env = gym.make(
        "PickCube-v1",
        num_envs=1,
        obs_mode="rgbd",
        control_mode="pd_ee_delta_pose",
        render_mode="rgb_array",
        sensor_configs=dict(width=512, height=512)
    )
    obs, info = env.reset(seed=0)
    report: dict[str, Any] = {
        "observation_space": str(env.observation_space),
        "reset_info_keys": sorted(list(info.keys())),
    }

    sensor_data = obs.get("sensor_data", {}) if isinstance(obs, dict) else {}
    camera_name = next(iter(sensor_data.keys())) if sensor_data else None
    report["camera_name"] = camera_name
    if camera_name is not None:
        cam = sensor_data[camera_name]
        report["camera_keys"] = sorted(list(cam.keys()))
        if "rgb" in cam:
            _save_png(out_dir / "maniskill_pickcube_rgb.png", cam["rgb"])
        if "depth" in cam:
            _save_depth_png(out_dir / "maniskill_pickcube_depth.png", cam["depth"])
        # if "rgb" in cam:
        #     _save_png(out_dir / "maniskill_pickcube_rgb.png", cam["rgb"], resize_to=(512, 512))
        # if "depth" in cam:
        #     _save_depth_png(out_dir / "maniskill_pickcube_depth.png", cam["depth"], resize_to=(512, 512))
    env.close()
    return report


def probe_control_modes(gym: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for control_mode in [
        "pd_joint_pos",
        "pd_joint_delta_pos",
        "pd_ee_delta_pos",
        "pd_ee_delta_pose",
    ]:
        env = gym.make(
            "PickCube-v1",
            num_envs=1,
            obs_mode="state",
            control_mode=control_mode,
        )
        result[control_mode] = str(env.action_space)
        env.close()
    return result


def probe_vector(gym: Any, out_dir: Path, num_envs: int) -> dict[str, Any]:
    env = gym.make(
        "PickCube-v1",
        obs_mode="state",
        control_mode="pd_ee_delta_pose",
        num_envs=num_envs,
    )
    lines = [_space_report(env)]
    obs, _ = env.reset(seed=0)
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated | truncated
    report = {
        "num_envs": num_envs,
        "obs_shape": list(_to_numpy(obs).shape),
        "reward_shape": list(_to_numpy(reward).shape),
        "done_shape": list(_to_numpy(done).shape),
        "reward_device": str(getattr(reward, "device", "numpy/cpu")),
        "reward_sample": _jsonable(reward[: min(num_envs, 8)]),
    }
    lines.append(json.dumps(report, ensure_ascii=False, indent=2))
    _write_text(out_dir / "maniskill_pickcube_vector.txt", "\n".join(lines) + "\n")
    _write_text(out_dir / "maniskill_pickcube_vector.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    env.close()
    return report


def probe_cpu_wrapper(gym: Any, out_dir: Path) -> dict[str, Any]:
    from mani_skill.utils.wrappers.gymnasium import CPUGymWrapper

    env = gym.make(
        "PickCube-v1",
        num_envs=1,
        obs_mode="state",
        control_mode="pd_ee_delta_pose",
    )
    env = CPUGymWrapper(env)
    obs, info = env.reset(seed=0)
    obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
    report = {
        "observation_space": str(env.observation_space),
        "action_space": str(env.action_space),
        "obs_type": type(obs).__name__,
        "obs_shape": list(np.asarray(obs).shape),
        "reward": reward,
        "reward_type": type(reward).__name__,
        "terminated_type": type(terminated).__name__,
        "truncated_type": type(truncated).__name__,
        "success": _jsonable(info.get("success")),
        "success_type": type(info.get("success")).__name__,
    }
    _write_text(out_dir / "maniskill_pickcube_wrapper.txt", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    env.close()
    return report




def run_vector_in_fresh_process(script_path: Path, out_dir: Path, num_envs: int) -> tuple[dict[str, Any] | None, str | None]:
    """Run the GPU/vector probe in a clean Python process.

    ManiSkill/SAPIEN GPU PhysX must be initialized before any other PhysX use in
    that process. Running the vector probe after CPU/render probes in the same
    process can raise: "GPU PhysX can only be enabled once before any other code
    involving PhysX". A child process avoids that initialization-order problem.
    """
    cmd = [
        sys.executable,
        str(script_path),
        "--only-vector",
        "--out-dir",
        str(out_dir),
        "--num-envs",
        str(num_envs),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        return None, f"Vector subprocess failed with exit code {proc.returncode}.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    vector_json = out_dir / "maniskill_pickcube_vector.json"
    if not vector_json.exists():
        return None, f"Vector subprocess finished but did not write {vector_json}."
    return json.loads(vector_json.read_text(encoding="utf-8")), None

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--num-envs", type=int, default=16)
    parser.add_argument("--skip-visual", action="store_true", help="Skip rgbd/render artifacts.")
    parser.add_argument("--skip-gpu", action="store_true", help="Skip num_envs>1 vector probe.")
    parser.add_argument("--only-vector", action="store_true", help="Run only the num_envs vector probe in this fresh process.")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    try:
        gym, _registered_envs, sapien = import_dependencies()
    except Exception as exc:
        msg = str(exc)
        _write_text(args.out_dir / "maniskill_pickcube.skipped", msg)
        print(msg, file=sys.stderr)
        return 1

    if args.only_vector:
        try:
            probe_vector(gym, args.out_dir, args.num_envs)
            return 0
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            _write_text(args.out_dir / "maniskill_pickcube_vector.skipped", msg)
            print(msg, file=sys.stderr)
            return 2

    summary: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for name, fn in [
        ("state_smoke", lambda: probe_state_smoke(gym, sapien, args.out_dir, args.steps)),
        ("control_modes", lambda: probe_control_modes(gym)),
        ("cpu_wrapper", lambda: probe_cpu_wrapper(gym, args.out_dir)),
    ]:
        try:
            summary[name] = fn()
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"

    if not args.skip_visual:
        try:
            summary["rgbd"] = probe_rgbd(gym, args.out_dir)
        except Exception as exc:
            errors["rgbd"] = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            _write_text(args.out_dir / "maniskill_pickcube_rgbd.skipped", errors["rgbd"])

    if not args.skip_gpu:
        vector_report, vector_error = run_vector_in_fresh_process(Path(__file__).resolve(), args.out_dir, args.num_envs)
        if vector_error is None:
            summary["vector"] = vector_report
        else:
            errors["vector"] = vector_error
            _write_text(args.out_dir / "maniskill_pickcube_vector.skipped", vector_error)

    summary["errors"] = errors
    _write_text(
        args.out_dir / "maniskill_pickcube_summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
