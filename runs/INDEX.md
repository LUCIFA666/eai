# `runs/` — Verified Experiment Outputs

This directory stores the **real** outputs of all `labs/*.py` scripts that
ship with the curriculum. Every "已验证" badge in the HTML chapters maps to
exactly one file here.

Last updated: 2026-05-20.
Environment: `/data/rbc/miniconda3/envs/lerobot` (python 3.10.20, mujoco 3.8.1,
gymnasium 1.2.3, torch 2.7.1+cu126, open3d 0.19.0, stable-baselines3 2.8.0,
dm_control 1.0.41, lerobot 0.4.4, transformers 5.8.1). Full snapshot in
[`check_env.md`](check_env.md).

## Chapter 02 — Environment & Toolchain

| File | What it proves |
|---|---|
| `02-environment/check_env.md` | Python / pkg version snapshot |
| `02-environment/cartpole_metrics.json` | 10-episode CartPole random rollout, length_mean=25.60 |
| `02-environment/determinism_check.json` | Two-run seed=0 trace identical for 85 steps |
| `02-environment/cartpole_rollout.{mp4,gif}` | 19-frame rollout video |
| `02-environment/rule_vs_random.md` | Rule beats random 40.90 vs 22.90 return |
| `02-environment/minigrid_demo.skipped` | Documents that minigrid env wasn't yet importable at run time |

## Chapter 03 — Robotics Foundations

| File | What it proves |
|---|---|
| `03-robotics/se3_transforms.txt` | SE(3) round-trip error 2.4e-16 |
| `03-robotics/two_link_fk_ik.txt` | 2-link FK/IK: 11/15 reachable targets |
| `03-robotics/pd_control.txt` | PD: rise/overshoot/settling on 3 (Kp,Kd) pairs |
| `03-robotics/pd_curve.csv` | Time-series PD trace for plotting |
| `03-robotics/mjcf_inspect_panda.txt` | Franka Panda MJCF: nq=9 nu=8 nbody=12 |
| `03-robotics/panda_fk.{txt,json}` | Panda FK on 5 canonical poses |
| `03-robotics/panda_dls_ik.csv` | DLS IK converged in 12 iters, final err 5.7e-05 m |
| `03-robotics/mujoco_inline_arm.txt` | Inline 3-link FK demo |
| `03-robotics/mujoco_inline_arm_ik.csv` | Singularity case: cond → 5.6e10 |

## Chapter 04 — Simulation Platforms

| File | What it proves |
|---|---|
| `04-simulation/custom_gym_env.{json,svg,txt}` | Custom Gymnasium env, random 0% / greedy 35% success |
| (more) | added by the section-04 build pass |

## Chapter 05 — Perception & 3D Vision

| File | What it proves |
|---|---|
| `05-perception/camera_calibration.txt` | Synthetic calibration, K err 0.000%, RMS 1.75e-05 px |
| `05-perception/rgbd_to_pointcloud.txt` + `.ply/.pcd/.png` | 306k/307k valid points, round-trip 3.05e-05 px |
| `05-perception/icp_demo.txt` + `icp_history.csv` | ICP alignment: 0.04° rotation / 0.14 mm translation |
| `05-perception/hand_eye_synthetic.txt` + `hand_eye_methods.csv` | 5 solvers, best ANDREFF 0.029°/0.626 mm |
| `05-perception/pnp_pose.txt` + `pnp_pose.csv` | PnP exact noiseless; RANSAC with 20% outliers 0.056°/4.21 mm |
| `05-perception/clip_zero_shot.txt` + `.csv` | CLIP ViT-B/32 4/4 on color squares |

## Chapter 06 — Planning, Control & Baselines

| File | What it proves |
|---|---|
| `06-planning/astar_gridworld.txt` + `astar_grid.csv` | A* 190 vs Dijkstra 682 expanded nodes |
| `06-planning/rrt_2d.txt` + `rrt_metrics.csv` + `rrt_star_path.csv` | RRT 16.31 m / RRT* 12.65 m |
| `06-planning/ilqr_pendulum.txt` + `.csv` | iLQR swing-up to 0.05° from upright |
| `06-planning/mpc_double_integrator.txt` + `.csv` | MPC 0.117 m RMS vs LQR 0.217 m RMS |

## Chapter 07 — Data, Teleoperation & IL

| File | What it proves |
|---|---|
| `07-data/inspect_dataset.txt` + `dataset_inspect.json` | LeRobot dataset inspection |
| `07-data/dataset_inspect.skipped` | Marks downloadable dataset as offline / network-bound |
| `07-data/cartpole_demos.{npz,txt}` | Scripted teleop dataset on CartPole |
| `07-data/scripted_demos.{npz,txt}` | Pendulum scripted demos |
| `07-data/bc_metrics.json` + `bc_pendulum.txt` | Behavior cloning on pendulum demos |

## Chapter 08 — Reinforcement Learning

| File | What it proves |
|---|---|
| `08-rl/ppo_cartpole.txt` + `.json` | SB3 PPO on CartPole-v1 |
| `08-rl/sac_pendulum.txt` + `.json` | SB3 SAC on Pendulum-v1 |
| `08-rl/reward_shaping.{json,txt}` | Comparison of dense vs sparse reward |
| `08-rl/cleanrl_ppo.txt` | CleanRL single-file PPO walkthrough output |

## Chapter 09 — VLM / VLA

| File | What it proves |
|---|---|
| `09-vla/clip_predictions.txt` | CLIP zero-shot on synthetic shapes |
| `09-vla/synthetic_shapes/` | The synthetic input images |

## Chapter 11 — Evaluation & Reproducibility

| File | What it proves |
|---|---|
| `11-eval/manifest_example.json` | Run manifest with content hash + git SHA + pkg versions |
| `11-eval/bootstrap_ci.{txt,json}` | success = 0.555 [0.485, 0.620] over 5 seeds × 40 ep |
| `11-eval/cartpole_success.mp4` + `cartpole_failure.mp4` | Recorded rollouts |
| `11-eval/tracked/.../config.yaml` | Hydra config example |
| `11-eval/smoke_test_runner.{txt,json}` | smoke test runs chapter-03 labs and asserts error < 1e-12 |

## Chapter 12 — Safety / Sim2Real / Capstone

| File | What it proves |
|---|---|
| `12-safety/dr_runs.{json,txt,csv}` | nominal=1.000, mild_dr=0.995, aggressive_dr=0.490 |
| `12-safety/sysid_pendulum.{txt,csv,json}` | Recovered length error 0.00%, damping err 1.39% |
| `12-safety/model_card_*` | Generated model card from fake checkpoint metadata |

## Reproducing Everything

```bash
cd /data/rbc/hands-on-embodied-ai
/data/rbc/miniconda3/envs/lerobot/bin/python labs/check_env.py | tee runs/check_env.md

# Chapter 03
for f in labs/03-robotics/*.py; do
  python "$f" 2>&1 | tee "runs/03-robotics/$(basename $f .py).rerun.txt"
done

# Chapter 11 smoke test runs the chapter-03 labs and validates outputs
python labs/11-eval/smoke_test_runner.py
```

If the chapter-03 labs do not reproduce, MuJoCo or numpy is mis-installed.
If chapter-11 smoke test fails, that is a regression — file a bug.
