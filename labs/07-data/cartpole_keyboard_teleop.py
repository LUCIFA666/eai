"""7.3 - Keyboard teleop on CartPole (with a headless scripted fallback).

If you have a display + pygame, this runs a real keyboard teleop:
  - LEFT arrow  -> action 0 (push cart left)
  - RIGHT arrow -> action 1 (push cart right)
  - SPACE       -> reset episode
  - Q           -> quit and save

Without a display we **fall back to a deterministic scripted "teleop"** that
plays a bang-bang stabiliser: ``a = 0 if angle < 0 else 1``. This is good
enough for collecting a BC dataset and means CI can produce ``cartpole_demos.npz``
without GUI.

Run:
    /data/rbc/miniconda3/envs/lerobot/bin/python labs/07-data/cartpole_keyboard_teleop.py

Outputs:
    runs/07-data/cartpole_demos.npz  (obs[N,4], act[N], ep_idx[N], returns[E])
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import gymnasium as gym
import numpy as np

OUT_PATH = Path("runs/07-data/cartpole_demos.npz")
N_EPISODES = 20


def has_display() -> bool:
    if not os.environ.get("DISPLAY"):
        return False
    try:
        import pygame  # noqa: F401
        return True
    except Exception:
        return False


def scripted_action(obs: np.ndarray, rng: np.random.Generator) -> int:
    """Bang-bang stabiliser with 5% epsilon-random for state coverage."""
    if rng.random() < 0.05:
        return int(rng.integers(0, 2))
    # obs = [x, x_dot, theta, theta_dot]; push right if pole leans right
    angle = obs[2]
    angular_vel = obs[3]
    # PD on angle + velocity feedback works better than pure sign-of-angle
    return 1 if (angle + 0.5 * angular_vel) > 0 else 0


def run_keyboard(env: gym.Env) -> tuple[list[np.ndarray], list[int], list[int], list[float]]:
    # Imported lazily to avoid crash in headless CI.
    import pygame  # type: ignore

    pygame.init()
    screen = pygame.display.set_mode((480, 120))
    pygame.display.set_caption("CartPole teleop  (←/→ to act, SPACE reset, Q quit)")
    font = pygame.font.SysFont(None, 22)
    obs_list, act_list, ep_idx, ep_returns = [], [], [], []
    ep, ret, done = 0, 0.0, False
    obs, _ = env.reset(seed=0)
    quitting = False
    while ep < N_EPISODES and not quitting:
        pressed = pygame.key.get_pressed()
        a = None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                quitting = True
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_q:
                quitting = True
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                done = True
        if pressed[pygame.K_LEFT]:
            a = 0
        elif pressed[pygame.K_RIGHT]:
            a = 1
        if a is None:
            a = 0 if obs[2] < 0 else 1  # default to scripted while idle
        obs_list.append(obs.copy()); act_list.append(a); ep_idx.append(ep)
        obs, r, term, trunc, _ = env.step(a)
        ret += r
        screen.fill((0, 0, 0))
        msg = font.render(f"ep {ep+1}/{N_EPISODES}  ret {ret:.0f}", True, (255, 255, 255))
        screen.blit(msg, (10, 40))
        pygame.display.flip()
        if term or trunc or done:
            ep_returns.append(ret); ep += 1; ret = 0.0; done = False
            obs, _ = env.reset()
    pygame.quit()
    return obs_list, act_list, ep_idx, ep_returns


def run_scripted(env: gym.Env) -> tuple[list[np.ndarray], list[int], list[int], list[float]]:
    rng = np.random.default_rng(0)
    obs_list, act_list, ep_idx, ep_returns = [], [], [], []
    for ep in range(N_EPISODES):
        obs, _ = env.reset(seed=ep)
        ret = 0.0
        done = False
        while not done:
            a = scripted_action(obs, rng)
            obs_list.append(obs.copy()); act_list.append(a); ep_idx.append(ep)
            obs, r, term, trunc, _ = env.step(a)
            ret += r
            done = term or trunc
        ep_returns.append(ret)
    return obs_list, act_list, ep_idx, ep_returns


def main() -> None:
    env = gym.make("CartPole-v1")
    mode_label: str
    runner: Callable[[gym.Env], tuple[list, list, list, list]]
    if has_display():
        mode_label = "keyboard (pygame)"
        runner = run_keyboard
    else:
        mode_label = "scripted (no DISPLAY)"
        runner = run_scripted

    obs_list, act_list, ep_idx, ep_returns = runner(env)
    env.close()

    obs = np.asarray(obs_list, dtype=np.float32)
    act = np.asarray(act_list, dtype=np.int64)
    epi = np.asarray(ep_idx, dtype=np.int32)
    rets = np.asarray(ep_returns, dtype=np.float32)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT_PATH, obs=obs, act=act, episode_index=epi, episode_return=rets,
             mode=np.array([mode_label]))

    print(f"mode          : {mode_label}")
    print(f"episodes      : {len(rets)}")
    print(f"obs shape     : {obs.shape}  (x, x_dot, theta, theta_dot)")
    print(f"act shape     : {act.shape}  (discrete left=0, right=1)")
    print(f"return mean   : {rets.mean():.1f}  (CartPole-v1 max=500)")
    print(f"return median : {np.median(rets):.1f}")
    print(f"return p10    : {np.percentile(rets, 10):.1f}")
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size/1024:.1f} KiB)")


if __name__ == "__main__":
    main()
