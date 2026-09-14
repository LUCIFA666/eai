"""Generate a ManiSkill task video gallery.

This script is intentionally evidence-oriented: a video only proves that a task
can be created, stepped, rendered, and recorded. The default action schedule is
a deterministic motion probe, not a policy, and should not be read as task
success.

Run from the repository root:
    python labs/04-simulation/maniskill_task_gallery.py --all

Run one task:
    python labs/04-simulation/maniskill_task_gallery.py --env-id PickCube-v1

Outputs:
    runs/04-simulation/maniskill_task_gallery/summary.json
    runs/04-simulation/maniskill_task_gallery/<env_id>/<env_id>.mp4
    runs/04-simulation/maniskill_task_gallery/<env_id>/<env_id>_reset.png
    runs/04-simulation/maniskill_task_gallery/<env_id>/summary.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = ROOT / "runs/04-simulation/maniskill_task_gallery"


def _to_numpy(x: Any) -> np.ndarray:
    if hasattr(x, "detach"):
        x = x.detach()
    if hasattr(x, "cpu"):
        x = x.cpu()
    if hasattr(x, "numpy"):
        return x.numpy()
    return np.asarray(x)


def _jsonable(x: Any) -> Any:
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


def _normalize_rgb(frame: Any) -> np.ndarray:
    arr = _to_numpy(frame)
    if arr.ndim == 4 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.ndim != 3:
        raise ValueError(f"Expected HxWxC or 1xHxWxC frame, got {arr.shape}")
    if arr.shape[-1] == 4:
        arr = arr[..., :3]
    if arr.shape[-1] != 3:
        raise ValueError(f"Expected RGB/RGBA frame, got {arr.shape}")
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr


def _snapshot_rgb(frame: Any) -> np.ndarray:
    return _normalize_rgb(frame).copy()


def _save_png(path: Path, frame: Any) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(_normalize_rgb(frame)).save(path)
    print(f"[write] {path}")


def _save_video(path: Path, frames: list[Any], fps: int) -> None:
    import imageio.v2 as imageio

    path.parent.mkdir(parents=True, exist_ok=True)
    clean = [_snapshot_rgb(frame) for frame in frames]
    imageio.mimsave(path, clean, fps=fps, macro_block_size=1)
    print(f"[write] {path}")


def _motion_metrics(frames: list[Any], threshold: float) -> dict[str, Any]:
    clean = [_snapshot_rgb(frame).astype(np.float32) for frame in frames]
    if len(clean) < 2:
        return {
            "n_frames": len(clean),
            "mean_step_absdiff": 0.0,
            "max_step_absdiff": 0.0,
            "max_absdiff_from_first": 0.0,
            "motion_threshold": threshold,
            "motion_status": "too_few_frames",
        }

    step_diffs = [float(np.mean(np.abs(clean[i] - clean[i - 1]))) for i in range(1, len(clean))]
    first = clean[0]
    from_first = [float(np.mean(np.abs(frame - first))) for frame in clean[1:]]
    max_step = float(np.max(step_diffs))
    max_from_first = float(np.max(from_first))
    return {
        "n_frames": len(clean),
        "mean_step_absdiff": float(np.mean(step_diffs)),
        "max_step_absdiff": max_step,
        "max_absdiff_from_first": max_from_first,
        "motion_threshold": threshold,
        "motion_status": "moving" if max(max_step, max_from_first) >= threshold else "nearly_static",
    }


def _import_mani_skill() -> tuple[Any, Any]:
    import gymnasium as gym
    import mani_skill.envs  # noqa: F401  registers ManiSkill environments

    return gym, sys.modules["mani_skill.envs"]


TASK_HINTS = [
    "Cube",
    "Peg",
    "Cabinet",
    "Drawer",
    "Stack",
    "Push",
    "Pull",
    "Turn",
    "Open",
    "Pick",
    "Place",
    "Roll",
    "Faucet",
    "Poke",
    "Plug",
    "Assembling",
    "TwoRobot",
    "TriFinger",
    "YCB",
    "SO100",
    "Widow",
    "Unitree",
]


TASK_OBS_MODE_OVERRIDES = {
    "StackGreenCubeOnYellowCubeBakedTexInScene-v1": "rgb+segmentation",
}


def list_tasks() -> list[str]:
    gym, _ = _import_mani_skill()
    tasks: list[str] = []
    for env_id in sorted(gym.registry.keys()):
        spec = gym.registry[env_id]
        if spec.vector_entry_point is not None and any(hint in env_id for hint in TASK_HINTS):
            tasks.append(env_id)
    return sorted(set(tasks))


def _box_center_half(space: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    low = np.asarray(space.low, dtype=np.float32)
    high = np.asarray(space.high, dtype=np.float32)
    finite = np.isfinite(low) & np.isfinite(high)
    center = np.where(finite, (low + high) * 0.5, 0.0).astype(np.float32)
    half = np.where(finite, (high - low) * 0.5, 1.0).astype(np.float32)
    half = np.where(np.isfinite(half), half, 1.0).astype(np.float32)
    return low, high, center, half


def _probe_action(space: Any, step: int, mode: str) -> Any:
    if hasattr(space, "spaces") and isinstance(space.spaces, dict):
        return {key: _probe_action(subspace, step, mode) for key, subspace in space.spaces.items()}

    if not (hasattr(space, "low") and hasattr(space, "high") and hasattr(space, "shape")):
        return space.sample()

    if mode == "random":
        return space.sample()

    low, high, center, half = _box_center_half(space)
    action = center.copy()
    flat = action.reshape(-1)
    center_flat = center.reshape(-1)
    half_flat = half.reshape(-1)
    n = flat.size

    if mode == "zero":
        pass
    elif mode == "all_sine":
        action = center + 0.95 * half * np.sin(step * 0.16)
    elif mode == "axis_pulse":
        axis = (step // 20) % max(n, 1)
        sign = 1.0 if ((step // 10) % 2 == 0) else -1.0
        flat[axis] = center_flat[axis] + 0.95 * half_flat[axis] * sign
    elif mode == "block_pulse":
        sign = 1.0 if ((step // 30) % 2 == 0) else -1.0
        signs = np.where((np.arange(n) % 2) == 0, sign, -sign).astype(np.float32).reshape(action.shape)
        action = center + 0.9 * half * signs
    elif mode == "gripper_arm":
        sign = 1.0 if ((step // 30) % 2 == 0) else -1.0
        for i in range(min(7, n)):
            flat[i] = center_flat[i] + 0.8 * half_flat[i] * (1 if i % 2 == 0 else -1) * sign
        if n > 7:
            flat[-1] = center_flat[-1] - 0.95 * half_flat[-1] * sign
    elif mode == "single_joint_sweep":
        axis = (step // 40) % max(n, 1)
        flat[axis] = center_flat[axis] + 0.95 * half_flat[axis] * np.sin(step * 0.12)
    else:
        raise ValueError(f"Unknown action mode: {mode}")

    return np.clip(action, low, high).astype(space.dtype)


def _safe_action(env: Any, step: int, action_mode: str) -> Any:
    return _probe_action(env.action_space, step, action_mode)


def _obs_mode_for(env_id: str, obs_mode: str) -> str:
    if obs_mode != "auto":
        return obs_mode
    return TASK_OBS_MODE_OVERRIDES.get(env_id, "state")


def run_one(
    env_id: str,
    out_dir: Path,
    steps: int,
    fps: int,
    frame_stride: int,
    obs_mode: str,
    action_mode: str,
    stop_on_done: bool,
    motion_threshold: float,
) -> int:
    gym, _ = _import_mani_skill()
    task_dir = out_dir / env_id.replace("/", "_")
    task_dir.mkdir(parents=True, exist_ok=True)
    skipped = task_dir / f"{env_id}.skipped"
    report_path = task_dir / "summary.json"

    env = None
    frames: list[Any] = []
    rewards: list[float] = []
    success_values: list[Any] = []
    resolved_obs_mode = _obs_mode_for(env_id, obs_mode)
    try:
        env = gym.make(env_id, obs_mode=resolved_obs_mode, render_mode="rgb_array", num_envs=1)
        report: dict[str, Any] = {
            "env_id": env_id,
            "obs_mode": resolved_obs_mode,
            "action_mode": action_mode,
            "stop_on_done": stop_on_done,
            "observation_space": str(env.observation_space),
            "action_space": str(env.action_space),
        }
        if hasattr(env, "single_observation_space"):
            report["single_observation_space"] = str(env.single_observation_space)
        if hasattr(env, "single_action_space"):
            report["single_action_space"] = str(env.single_action_space)

        obs, info = env.reset(seed=0)
        report["reset_info_keys"] = sorted(list(info.keys()))
        report["obs_after_reset"] = _jsonable(obs)
        _save_png(task_dir / f"{env_id}_reset.png", env.render())

        done_count = 0
        frames.append(_snapshot_rgb(env.render()))
        for step in range(steps):
            obs, reward, terminated, truncated, info = env.step(_safe_action(env, step, action_mode))
            rewards.append(float(_to_numpy(reward).reshape(-1)[0]))
            if "success" in info:
                success_values.append(_jsonable(info["success"]))
            if step % frame_stride == 0:
                frames.append(_snapshot_rgb(env.render()))
            done = np.asarray(_to_numpy(terminated) | _to_numpy(truncated)).reshape(-1)
            if done.any():
                done_count += 1
                if stop_on_done:
                    break

        if frames:
            _save_video(task_dir / f"{env_id}.mp4", frames, fps=fps)
        motion = _motion_metrics(frames, threshold=motion_threshold)
        report.update(
            {
                "status": "ok",
                "n_steps": len(rewards),
                "done_count": done_count,
                "mean_reward_probe": float(np.mean(rewards)) if rewards else None,
                "max_reward_probe": float(np.max(rewards)) if rewards else None,
                "last_success": success_values[-1] if success_values else None,
                "video": str(task_dir / f"{env_id}.mp4"),
                "reset_png": str(task_dir / f"{env_id}_reset.png"),
                "motion": motion,
            }
        )
        _write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        if skipped.exists():
            skipped.unlink()
        return 0
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        _write_text(skipped, msg)
        _write_text(
            report_path,
            json.dumps({"env_id": env_id, "status": "skipped", "error": msg}, ensure_ascii=False, indent=2) + "\n",
        )
        print(msg, file=sys.stderr)
        return 2
    finally:
        if env is not None:
            try:
                env.close()
            except Exception:
                pass


def run_batch(args: argparse.Namespace) -> int:
    tasks = args.tasks or list_tasks()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for i, env_id in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {env_id}")
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--env-id",
            env_id,
            "--out-dir",
            str(args.out_dir),
            "--steps",
            str(args.steps),
            "--fps",
            str(args.fps),
            "--frame-stride",
            str(args.frame_stride),
            "--obs-mode",
            args.obs_mode,
            "--action-mode",
            args.action_mode,
            "--motion-threshold",
            str(args.motion_threshold),
        ]
        if args.stop_on_done:
            cmd.append("--stop-on-done")
        try:
            proc = subprocess.run(cmd, text=True, capture_output=True, timeout=args.timeout)
            if proc.stdout:
                print(proc.stdout, end="")
            if proc.stderr:
                print(proc.stderr, end="", file=sys.stderr)
            task_report = args.out_dir / env_id.replace("/", "_") / "summary.json"
            if task_report.exists():
                reports.append(json.loads(task_report.read_text(encoding="utf-8")))
            else:
                reports.append({"env_id": env_id, "status": "missing_report", "returncode": proc.returncode})
        except subprocess.TimeoutExpired as exc:
            task_dir = args.out_dir / env_id.replace("/", "_")
            task_dir.mkdir(parents=True, exist_ok=True)
            msg = f"Timed out after {args.timeout} seconds."
            _write_text(task_dir / f"{env_id}.skipped", msg + "\n")
            _write_text(
                task_dir / "summary.json",
                json.dumps({"env_id": env_id, "status": "timeout", "error": msg}, ensure_ascii=False, indent=2) + "\n",
            )
            reports.append({"env_id": env_id, "status": "timeout", "error": msg})
            if exc.stdout:
                print(exc.stdout, end="")
            if exc.stderr:
                print(exc.stderr, end="", file=sys.stderr)

    summary = {
        "n_tasks": len(reports),
        "ok": sum(1 for r in reports if r.get("status") == "ok"),
        "skipped": sum(1 for r in reports if r.get("status") != "ok"),
        "moving": sum(1 for r in reports if r.get("motion", {}).get("motion_status") == "moving"),
        "nearly_static": sum(1 for r in reports if r.get("motion", {}).get("motion_status") == "nearly_static"),
        "too_few_frames": sum(1 for r in reports if r.get("motion", {}).get("motion_status") == "too_few_frames"),
        "note": "Videos are deterministic motion probes for visual checking; they are not successful task policies.",
        "tasks": reports,
    }
    _write_text(args.out_dir / "summary.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return 0 if summary["skipped"] == 0 else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--all", action="store_true", help="Run all discovered ManiSkill manipulation tasks.")
    parser.add_argument("--env-id", help="Run one task.")
    parser.add_argument("--tasks", nargs="*", help="Explicit task list for batch mode.")
    parser.add_argument("--list", action="store_true", help="List discovered task ids.")
    parser.add_argument("--steps", type=int, default=160)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--frame-stride", type=int, default=4)
    parser.add_argument(
        "--obs-mode",
        default="auto",
        help="Observation mode to request. Use 'auto' for task-specific fallbacks.",
    )
    parser.add_argument(
        "--action-mode",
        default="all_sine",
        choices=["random", "zero", "all_sine", "axis_pulse", "block_pulse", "gripper_arm", "single_joint_sweep"],
        help="Action schedule for visual motion probes. These are not task policies.",
    )
    parser.add_argument(
        "--stop-on-done",
        action="store_true",
        help="Stop recording at terminated/truncated. Default keeps recording to make motion visible.",
    )
    parser.add_argument(
        "--motion-threshold",
        type=float,
        default=1.0,
        help="Minimum mean absolute RGB frame difference used to mark a video as moving.",
    )
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    if args.list:
        for env_id in list_tasks():
            print(env_id)
        return 0
    if args.env_id:
        return run_one(
            args.env_id,
            args.out_dir,
            args.steps,
            args.fps,
            args.frame_stride,
            args.obs_mode,
            args.action_mode,
            args.stop_on_done,
            args.motion_threshold,
        )
    if args.all or args.tasks:
        return run_batch(args)
    parser.error("Use --list, --env-id ENV_ID, --tasks ..., or --all.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
