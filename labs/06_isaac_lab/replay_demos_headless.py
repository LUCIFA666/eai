"""Replay Isaac Lab HDF5 demos without keyboard/window dependencies.

The upstream ``scripts/tools/replay_demos.py`` is useful for interactive
inspection, but it creates a ``Se3Keyboard`` even when run headless. On servers
without an app window this can fail before the dataset is actually replayed.

This script is intentionally smaller: it replays selected episodes from an HDF5
dataset, optionally evaluates the task success term, and always prints summary
statistics before exiting.

Example:

    ./isaaclab.sh -p labs/06_isaac_lab/replay_demos_headless.py \
        --dataset_file datasets/dataset.hdf5 \
        --select_episodes 0 \
        --validate_success_rate \
        --headless
"""

from __future__ import annotations

import argparse
import os

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Replay HDF5 demos without keyboard/window dependencies.")
parser.add_argument("--task", type=str, default=None, help="Override task id. Defaults to env name stored in dataset.")
parser.add_argument("--dataset_file", type=str, default="datasets/dataset.hdf5", help="HDF5 dataset file.")
parser.add_argument("--select_episodes", type=int, nargs="+", default=[], help="Episode indices to replay.")
parser.add_argument("--validate_success_rate", action="store_true", default=False, help="Evaluate success term.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import gymnasium as gym  # noqa: E402
import torch  # noqa: E402

import isaaclab_tasks  # noqa: F401, E402
from isaaclab_tasks.utils.parse_cfg import parse_env_cfg  # noqa: E402
from isaaclab.utils.datasets import HDF5DatasetFileHandler  # noqa: E402


def main() -> None:
    if not os.path.exists(args_cli.dataset_file):
        raise FileNotFoundError(f"The dataset file {args_cli.dataset_file} does not exist.")

    dataset = HDF5DatasetFileHandler()
    dataset.open(args_cli.dataset_file)

    env_name = args_cli.task or dataset.get_env_name()
    if env_name is None:
        raise ValueError("Task/env name was not provided and was not found in the dataset.")

    episode_names = list(dataset.get_episode_names())
    episode_count = len(episode_names)
    if episode_count == 0:
        print("No episodes found in the dataset.", flush=True)
        return

    episode_indices = args_cli.select_episodes or list(range(episode_count))
    episode_indices = [index for index in episode_indices if 0 <= index < episode_count]
    if not episode_indices:
        raise ValueError(f"No valid episode indices were selected. Dataset has {episode_count} episodes.")

    env_cfg = parse_env_cfg(env_name, device=args_cli.device, num_envs=1)
    success_term = None
    if args_cli.validate_success_rate:
        if hasattr(env_cfg.terminations, "success"):
            success_term = env_cfg.terminations.success
        else:
            print("No success termination term was found; success rate will not be reported.", flush=True)

    # Avoid recorder side effects and automatic termination during replay.
    env_cfg.recorders = {}
    env_cfg.terminations = {}

    env = gym.make(env_name, cfg=env_cfg).unwrapped
    env.reset()

    replayed = 0
    successful = 0
    failed: list[int] = []

    with torch.inference_mode():
        for episode_index in episode_indices:
            episode_name = episode_names[episode_index]
            episode = dataset.load_episode(episode_name, env.device)
            initial_state = episode.get_initial_state()
            env.reset_to(initial_state, torch.tensor([0], device=env.device), is_relative=True)

            action_count = 0
            while simulation_app.is_running() and not simulation_app.is_exiting():
                action = episode.get_next_action()
                if action is None:
                    break
                if action.ndim == 1:
                    action = action.unsqueeze(0)
                env.step(action)
                action_count += 1

            replayed += 1
            is_success = None
            if success_term is not None:
                is_success = bool(success_term.func(env, **success_term.params)[0].item())
                if is_success:
                    successful += 1
                else:
                    failed.append(episode_index)

            print(
                f"Replayed episode #{episode_index} ({episode_name}) with {action_count} actions"
                + (f"; success={is_success}" if is_success is not None else ""),
                flush=True,
            )

    print(f"Finished replaying {replayed} episode{'s' if replayed != 1 else ''}.", flush=True)
    if success_term is not None:
        print(f"Successfully replayed: {successful}/{replayed}", flush=True)
        if failed:
            print(f"Failed demo IDs ({len(failed)} total): {failed}", flush=True)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close(wait_for_replicator=False, skip_cleanup=True)
