import argparse
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

import simpler_env
from simpler_env.utils.env.observation_utils import get_image_from_maniskill2_obs_dict


def get_instruction(env):
    try:
        return env.unwrapped.get_language_instruction()
    except Exception:
        return env.get_language_instruction()


def write_video(mp4_path: Path, frames, fps: int) -> str:
    """优先保存 mp4；本机缺少 ffmpeg 时退回 gif。"""
    try:
        imageio.mimsave(mp4_path, frames, fps=fps)
        return str(mp4_path)
    except Exception as exc:
        gif_path = mp4_path.with_suffix(".gif")
        print("[WARN] MP4 保存失败，改为保存 GIF:", repr(exc), flush=True)
        imageio.mimsave(gif_path, frames, fps=fps)
        return str(gif_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="google_robot_pick_coke_can")
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fps", type=int, default=5)
    parser.add_argument("--out-dir", default="runs/11-eval/simplerenv_rollout_video_zero")
    parser.add_argument(
        "--action-mode",
        choices=["zero", "small-random"],
        default="zero",
        help="zero 用于稳定 smoke test；small-random 用于观察动作接口。",
    )
    parser.add_argument("--action-scale", type=float, default=0.02)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    out_dir = Path(args.out_dir)
    frame_dir = out_dir / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)

    print("[1] create env", flush=True)
    env = simpler_env.make(args.task)

    print("[2] reset", flush=True)
    obs, reset_info = env.reset()
    instruction = get_instruction(env)

    frames = []
    records = []

    image = get_image_from_maniskill2_obs_dict(env, obs)
    frames.append(image)
    imageio.imwrite(frame_dir / "frame_000.png", image)

    print("Instruction:", instruction, flush=True)
    print("Action space:", env.action_space, flush=True)
    print("Observation keys:", obs.keys(), flush=True)
    print("Initial image shape:", image.shape, image.dtype, flush=True)

    for step in range(args.steps):
        print(f"[3] step {step}", flush=True)
        action = np.zeros(env.action_space.shape, dtype=env.action_space.dtype)

        if args.action_mode == "small-random":
            # 只扰动末端位置；旋转和夹爪保持 0，避免入门示例里动作过激。
            action[:3] = rng.uniform(
                -args.action_scale,
                args.action_scale,
                size=3,
            ).astype(env.action_space.dtype)

        action = np.clip(action, env.action_space.low, env.action_space.high)
        obs, reward, terminated, truncated, info = env.step(action)

        image = get_image_from_maniskill2_obs_dict(env, obs)
        frames.append(image)
        imageio.imwrite(frame_dir / f"frame_{step + 1:03d}.png", image)

        records.append({
            "step": step,
            "action": action.tolist(),
            "reward": float(reward),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "success": bool(info.get("success", False)),
            "episode_stats": str(info.get("episode_stats", {})),
        })

        if terminated or truncated:
            break

    video_path = write_video(out_dir / "rollout.mp4", frames, fps=args.fps)

    result = {
        "task": args.task,
        "seed": args.seed,
        "instruction": instruction,
        "action_mode": args.action_mode,
        "action_scale": args.action_scale,
        "action_space": str(env.action_space),
        "reset_info": str(reset_info),
        "num_frames": len(frames),
        "video": video_path,
        "frames_dir": str(frame_dir),
        "records": records,
    }

    with open(out_dir / "result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("[4] saved result", flush=True)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)

    env.close()
    print("[5] env closed", flush=True)


if __name__ == "__main__":
    main()
