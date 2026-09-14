import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

import simpler_env
from simpler_env.utils.env.observation_utils import get_image_from_maniskill2_obs_dict


def get_instruction(env):
    """兼容 gymnasium wrapper 的写法。"""
    try:
        return env.unwrapped.get_language_instruction()
    except Exception:
        return env.get_language_instruction()


out_dir = Path("runs/11-eval/simplerenv_step_debug")
out_dir.mkdir(parents=True, exist_ok=True)

task = "google_robot_pick_coke_can"

print("[1] creating env", flush=True)
env = simpler_env.make(task)

print("[2] reset", flush=True)
obs, reset_info = env.reset()

print("[3] get first image", flush=True)
img0 = get_image_from_maniskill2_obs_dict(env, obs)
imageio.imwrite(out_dir / "step_000_reset.png", img0)

print("[4] language instruction", flush=True)
instruction = get_instruction(env)

print("Instruction:", instruction, flush=True)
print("Action space:", env.action_space, flush=True)
print("Observation keys:", obs.keys(), flush=True)
print("Image shape:", img0.shape, img0.dtype, flush=True)

print("[5] env.step with zero action", flush=True)
action = np.zeros(env.action_space.shape, dtype=env.action_space.dtype)
obs, reward, terminated, truncated, info = env.step(action)

print("[6] get image after step", flush=True)
img1 = get_image_from_maniskill2_obs_dict(env, obs)
imageio.imwrite(out_dir / "step_001_after_zero_action.png", img1)

result = {
    "task": task,
    "instruction": instruction,
    "action_space": str(env.action_space),
    "observation_keys": list(obs.keys()),
    "reset_info": str(reset_info),
    "reward_after_one_step": float(reward),
    "terminated": bool(terminated),
    "truncated": bool(truncated),
    "info": str(info),
    "saved_images": [
        str(out_dir / "step_000_reset.png"),
        str(out_dir / "step_001_after_zero_action.png"),
    ],
}

with open(out_dir / "result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("[7] result saved", flush=True)
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)

env.close()
print("[8] env closed", flush=True)
