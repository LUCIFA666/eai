# RLINF 文件索引：envs

覆盖 `envs` 分组，共 `156` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/envs/__init__.py` | 132 | 仿真、benchmark、真机环境封装；公共入口/工具 | SupportedEnvType | get_env_cls | enum |
| `rlinf/envs/action_utils.py` | 297 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | prepare_actions_for_maniskill, prepare_actions_for_libero, prepare_actions_for_isaaclab, prepare_actions_for_calvin, prepare_actions_for_metaworld, prepare_actions_for_robocasa, prepare_actions_for_mujoco, prepare_actions_for_d4rl, prepare_actions_for_roboverse, prepare_actions | numpy, rlinf, torch |
| `rlinf/envs/behavior/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/behavior/behavior_env.py` | 648 | 仿真、benchmark、真机环境封装；环境适配 | BehaviorProcess, ThreadWithResult, BehaviorProcessProxy, BehaviorEnv | - | gc, gymnasium, inspect, json, multiprocessing, omegaconf, os, rlinf |
| `rlinf/envs/behavior/instance_generator.py` | 482 | 仿真、benchmark、真机环境封装 | - | parse_args, load_env_cfg, build_sampling_omni_cfg, resolve_output_dir, configure_sampling_macros, build_output_path, dump_tro_state, save_activity_instance, generate_activity_instances, main | argparse, json, omegaconf, pathlib, rlinf, sys |
| `rlinf/envs/behavior/instance_loader.py` | 479 | 仿真、benchmark、真机环境封装 | ActivityInstanceFile, ActivityInstanceLoader | parse_activity_instance_filename, discover_activity_instance_files, load_activity_instance_tro_state | dataclasses, json, omegaconf, os, pathlib, random, rlinf |
| `rlinf/envs/behavior/rgb_wrapper.py` | 40 | 仿真、benchmark、真机环境封装 | RGBWrapper | - | __future__, omnigibson |
| `rlinf/envs/behavior/utils.py` | 300 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | sync_robot_after_pose_override, set_camera_resolution, apply_runtime_renderer_settings, get_env_wrapper, convert_uint8_rgb, patch_omnigibson_wrapper_reset_signature, apply_env_wrapper, override_sub_cfg, setup_omni_cfg | inspect, omegaconf, os, rlinf, torch, yaml |
| `rlinf/envs/calvin/__init__.py` | 129 | 仿真、benchmark、真机环境封装；公共入口/工具 | CalvinBenchmark | _get_calvin_tasks_and_reward, make_env | calvin_agent, calvin_env, hydra, omegaconf, pathlib, rlinf |
| `rlinf/envs/calvin/calvin_gym_env.py` | 486 | 仿真、benchmark、真机环境封装；环境适配 | CalvinEnv | - | copy, gymnasium, numpy, os, rlinf, torch, typing |
| `rlinf/envs/calvin/utils.py` | 75 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | f, get_sequences | calvin_agent, concurrent, functools, itertools, multiprocessing, numpy |
| `rlinf/envs/calvin/venv.py` | 264 | 仿真、benchmark、真机环境封装；环境适配 | ReconfigureSubprocEnvWorker, ReconfigureSubprocEnv | _worker | gymnasium, multiprocessing, numpy, rlinf, typing, warnings |
| `rlinf/envs/d4rl/__init__.py` | 17 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | rlinf |
| `rlinf/envs/d4rl/d4rl_env.py` | 578 | 仿真、benchmark、真机环境封装；环境适配 | D4RLEnv | _cfg_get, _to_info_list | copy, d4rl, gym, numpy, rlinf, time, torch, typing |
| `rlinf/envs/embodichain/__init__.py` | 17 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | rlinf |
| `rlinf/envs/embodichain/embodichain_env.py` | 477 | 仿真、benchmark、真机环境封装；环境适配 | EmbodiChainEnv | _resolve_gym_config_path, _cfg_get, _resolve_sim_device_and_gpu_id, _clone_nested, _masked_update | copy, gymnasium, numpy, os, pathlib, torch, typing |
| `rlinf/envs/frankasim/__init__.py` | 19 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | franka_sim, frankasim_env |
| `rlinf/envs/frankasim/frankasim_env.py` | 722 | 仿真、benchmark、真机环境封装；环境适配 | FrankaSimEnv | _unwrap_object_scalar, _flatten_any_safe, extract_serl_state, extract_serl_images_dict, _cfg_get, _torch_clone_dict | copy, gym, numpy, torch, typing |
| `rlinf/envs/habitat/__init__.py` | 17 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | habitat_env |
| `rlinf/envs/habitat/extensions/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/habitat/extensions/maps.py` | 357 | 仿真、benchmark、真机环境封装 | - | get_top_down_map, colorize_topdown_map, static_to_grid, drawline, drawpoint, draw_triangle, draw_reference_path, draw_straight_shortest_path_points, draw_source_and_target, draw_waypoint_prediction | habitat, networkx, numpy, typing |
| `rlinf/envs/habitat/extensions/utils.py` | 711 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | observations_to_image, pano_observations_to_image, add_id_on_img, add_instruction_on_img, add_step_stats_on_img, add_prob_on_img, add_stop_prob_on_img, waypoint_observations_to_image, navigator_video_frame, compute_heading_to | copy, habitat, habitat_sim, numpy, quaternion, rlinf, textwrap, torch |
| `rlinf/envs/habitat/habitat_env.py` | 348 | 仿真、benchmark、真机环境封装；环境适配 | NoOpAction, HabitatEnv | - | copy, gym, habitat, habitat_baselines, hydra, numpy, rlinf, torch |
| `rlinf/envs/habitat/venv.py` | 246 | 仿真、benchmark、真机环境封装；环境适配 | HabitatRLEnv, ReconfigureSubprocEnvWorker, ReconfigureSubprocEnv | _worker | gym, habitat, multiprocessing, numpy, rlinf, typing, warnings |
| `rlinf/envs/isaaclab/__init__.py` | 21 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | tasks |
| `rlinf/envs/isaaclab/isaaclab_env.py` | 264 | 仿真、benchmark、真机环境封装；环境适配 | IsaaclabBaseEnv | - | copy, gymnasium, omegaconf, rlinf, torch, typing |
| `rlinf/envs/isaaclab/tasks/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/isaaclab/tasks/stack_cube.py` | 100 | 仿真、benchmark、真机环境封装 | IsaaclabStackCubeEnv | - | gymnasium, isaaclab_env, rlinf, torch |
| `rlinf/envs/isaaclab/utils.py` | 62 | 仿真、benchmark、真机环境封装；公共入口/工具 | CloudpickleWrapper | quat2axisangle_torch | cloudpickle, pickle, torch |
| `rlinf/envs/isaaclab/venv.py` | 118 | 仿真、benchmark、真机环境封装；环境适配 | SubProcIsaacLabEnv | _torch_worker | multiprocessing, torch, utils |
| `rlinf/envs/libero/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/libero/libero_env.py` | 767 | 仿真、benchmark、真机环境封装；环境适配 | LiberoEnv | - | copy, glob, gym, importlib, numpy, omegaconf, os, rlinf |
| `rlinf/envs/libero/utils.py` | 175 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | get_libero_type, get_libero_image, get_libero_wrist_image, quat2axisangle, get_benchmark_overridden | math, numpy, os, typing |
| `rlinf/envs/libero/venv.py` | 211 | 仿真、benchmark、真机环境封装；环境适配 | ReconfigureSubprocEnvWorker, ReconfigureSubprocEnv | _worker | gym, multiprocessing, numpy, rlinf, typing, warnings |
| `rlinf/envs/maniskill/__init__.py` | 33 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | import_all_tasks | importlib, pathlib, pkgutil |
| `rlinf/envs/maniskill/maniskill_env.py` | 436 | 仿真、benchmark、真机环境封装；环境适配 | ManiskillEnv | extract_termination_from_info | gymnasium, mani_skill, numpy, omegaconf, torch, typing |
| `rlinf/envs/maniskill/maniskill_offload_env.py` | 445 | 仿真、benchmark、真机环境封装；环境适配 | EnvOffloadMixin, _ManiskillEnvCore, ManiskillOffloadEnv | _maniskill_worker_main | io, rlinf, torch, traceback, typing |
| `rlinf/envs/maniskill/tasks/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/maniskill/tasks/panda_put_on_in_scene_multi.py` | 1382 | 仿真、benchmark、真机环境封装 | PandaPutOnPlateInScene25, PandaPutOnPlateInScene25DigitalTwin | - | cv2, mani_skill, numpy, os, pathlib, rlinf, sapien, torch |
| `rlinf/envs/maniskill/tasks/panda_table_agent.py` | 136 | 仿真、benchmark、真机环境封装 | PandaBridgeDatasetFlatTable | - | copy, mani_skill, numpy, sapien |
| `rlinf/envs/maniskill/tasks/pick_cube_3view.py` | 38 | 仿真、benchmark、真机环境封装 | PickCube3ViewEnv | - | mani_skill, numpy |
| `rlinf/envs/maniskill/tasks/pose_utils.py` | 311 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | pose_inv, quat2euler, pose2matrix, pose2matrix_torch, matrix2pose, pose2matrix_batch, pose2matrix_batch_torch, matrix2pose_batch, matrix2pose_batch_torch | numpy, scipy, torch |
| `rlinf/envs/maniskill/tasks/put_carrot_on_plate.py` | 151 | 仿真、benchmark、真机环境封装 | PutCarrotOnPlateInSceneV2 | - | mani_skill, numpy, sapien, torch |
| `rlinf/envs/maniskill/tasks/put_on_in_scene_multi.py` | 963 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25, PutOnPlateInScene25MainV3 | - | cv2, mani_skill, numpy, os, pathlib, sapien, torch, transforms3d |
| `rlinf/envs/maniskill/tasks/variants/__init__.py` | 51 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | put_on_plate_25_carrot, put_on_plate_25_ee_pose, put_on_plate_25_image, put_on_plate_25_instruct, put_on_plate_25_multi_carrot, put_on_plate_25_multi_plate, put_on_plate_25_plate, put_on_plate_25_position |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_carrot.py` | 77 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25MainCarrotV3, PutOnPlateInScene25Carrot | - | mani_skill, rlinf |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_ee_pose.py` | 289 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25EEPose | - | itertools, mani_skill, numpy, rlinf, torch |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_image.py` | 105 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25MainImageV3 | - | cv2, mani_skill, rlinf |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_instruct.py` | 123 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25Instruct | - | mani_skill, rlinf, torch |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_multi_carrot.py` | 352 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25MultiCarrot | - | mani_skill, numpy, rlinf, torch, transforms3d |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_multi_plate.py` | 399 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25MultiPlate | - | cv2, mani_skill, numpy, rlinf, torch, transforms3d |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_plate.py` | 97 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25Plate | - | cv2, mani_skill, rlinf |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_position.py` | 231 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25Position | - | mani_skill, numpy, rlinf, torch, transforms3d |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_position_change.py` | 179 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25PositionChange | - | mani_skill, numpy, rlinf, torch, transforms3d |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_single.py` | 110 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25Single | - | cv2, mani_skill, rlinf |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_vision_image.py` | 49 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25VisionImage | - | mani_skill, rlinf |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_vision_texture.py` | 325 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25VisionTexture03, PutOnPlateInScene25VisionTexture05 | - | mani_skill, rlinf, torch |
| `rlinf/envs/maniskill/tasks/variants/put_on_plate_25_vision_whole.py` | 364 | 仿真、benchmark、真机环境封装 | PutOnPlateInScene25VisionWhole03, PutOnPlateInScene25VisionWhole05 | - | cv2, mani_skill, rlinf, torch |
| `rlinf/envs/maniskill/tasks/variants/utils.py` | 31 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | masks_to_boxes_pytorch | torch |
| `rlinf/envs/maniskill/utils.py` | 66 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | recursive_to_own, force_gc_tensor, cleanup_cuda_tensors, get_batch_rng_state, set_batch_rng_state | ctypes, gc, sys, torch |
| `rlinf/envs/metaworld/__init__.py` | 61 | 仿真、benchmark、真机环境封装；公共入口/工具 | MetaWorldBenchmark | - | os, rlinf |
| `rlinf/envs/metaworld/metaworld_env.py` | 442 | 仿真、benchmark、真机环境封装；环境适配 | MetaWorldEnv | - | copy, gymnasium, metaworld, numpy, os, rlinf, torch, typing |
| `rlinf/envs/metaworld/utils.py` | 21 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | load_prompt_from_json | json |
| `rlinf/envs/metaworld/venv.py` | 170 | 仿真、benchmark、真机环境封装；环境适配 | ReconfigureSubprocEnvWorker, ReconfigureSubprocEnv | _worker | gymnasium, multiprocessing, numpy, rlinf, typing, warnings |
| `rlinf/envs/realworld/__init__.py` | 47 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | dosw1, franka, gim_arm, realworld_env, xsquare |
| `rlinf/envs/realworld/common/camera/__init__.py` | 48 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | create_camera | base_camera, realsense_camera |
| `rlinf/envs/realworld/common/camera/base_camera.py` | 110 | 仿真、benchmark、真机环境封装 | CameraInfo, BaseCamera | - | abc, dataclasses, numpy, queue, threading, time, typing |
| `rlinf/envs/realworld/common/camera/lumos_camera.py` | 156 | 仿真、benchmark、真机环境封装 | LumosCamera | - | base_camera, glob, numpy, os, rlinf, typing |
| `rlinf/envs/realworld/common/camera/realsense_camera.py` | 100 | 仿真、benchmark、真机环境封装 | RealSenseCamera | - | base_camera, numpy, typing |
| `rlinf/envs/realworld/common/camera/zed_camera.py` | 138 | 仿真、benchmark、真机环境封装 | ZEDCamera | - | base_camera, numpy, rlinf, typing |
| `rlinf/envs/realworld/common/gello/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/realworld/common/gello/gello_expert.py` | 101 | 仿真、benchmark、真机环境封装 | GelloExpert | - | numpy, threading |
| `rlinf/envs/realworld/common/glove/__init__.py` | 15 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/realworld/common/glove/glove_expert.py` | 23 | 仿真、benchmark、真机环境封装 | - | - | rlinf_dexhand |
| `rlinf/envs/realworld/common/gripper/__init__.py` | 62 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | create_gripper | base_gripper, typing |
| `rlinf/envs/realworld/common/gripper/base_gripper.py` | 74 | 仿真、benchmark、真机环境封装 | BaseGripper | - | abc |
| `rlinf/envs/realworld/common/gripper/franka_gripper.py` | 103 | 仿真、benchmark、真机环境封装 | FrankaGripper | - | base_gripper, numpy |
| `rlinf/envs/realworld/common/gripper/robotiq_gripper.py` | 234 | 仿真、benchmark、真机环境封装 | RobotiqGripper | _create_modbus_client | base_gripper, inspect, numpy, rlinf, time, typing |
| `rlinf/envs/realworld/common/hand/__init__.py` | 17 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | ruiyan_hand |
| `rlinf/envs/realworld/common/hand/ruiyan_hand.py` | 132 | 仿真、benchmark、真机环境封装 | RuiyanHand | - | numpy, rlinf, typing |
| `rlinf/envs/realworld/common/keyboard/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/realworld/common/keyboard/keyboard_listener.py` | 164 | 仿真、benchmark、真机环境封装 | KeyboardListener | - | os, threading |
| `rlinf/envs/realworld/common/ros/__init__.py` | 17 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | ros_controller |
| `rlinf/envs/realworld/common/ros/ros_controller.py` | 129 | 仿真、benchmark、真机环境封装 | ROSController | - | filelock, os, pathlib, psutil, rlinf, rospy, sys, time |
| `rlinf/envs/realworld/common/spacemouse/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/realworld/common/spacemouse/spacemouse_expert.py` | 70 | 仿真、benchmark、真机环境封装 | SpaceMouseExpert | - | numpy, threading |
| `rlinf/envs/realworld/common/video_player/__init__.py` | 17 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | video_player |
| `rlinf/envs/realworld/common/video_player/video_player.py` | 55 | 仿真、benchmark、真机环境封装 | VideoPlayer | - | cv2, numpy, os, queue, threading, warnings |
| `rlinf/envs/realworld/common/wrappers/__init__.py` | 74 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | __getattr__ | apply, dual_euler_obs, dual_gello_intervention, dual_relative_frame, dual_spacemouse_intervention, euler_obs, gello_intervention, gripper_close |
| `rlinf/envs/realworld/common/wrappers/apply.py` | 174 | 仿真、benchmark、真机环境封装 | - | _load_dexhand_intervention, _validate_teleop_mode, _apply_keyboard_reward, apply_single_arm_wrappers, apply_dual_arm_wrappers | __future__, gymnasium, rlinf, typing |
| `rlinf/envs/realworld/common/wrappers/dexhand_intervention.py` | 128 | 仿真、benchmark、真机环境封装 | DexHandIntervention | - | __future__, gymnasium, numpy, rlinf, time, typing |
| `rlinf/envs/realworld/common/wrappers/dual_euler_obs.py` | 47 | 仿真、benchmark、真机环境封装 | DualQuat2EulerWrapper | - | gymnasium, numpy, scipy |
| `rlinf/envs/realworld/common/wrappers/dual_gello_intervention.py` | 116 | 仿真、benchmark、真机环境封装 | DualGelloIntervention | - | __future__, gymnasium, numpy, rlinf, scipy, time |
| `rlinf/envs/realworld/common/wrappers/dual_relative_frame.py` | 159 | 仿真、benchmark、真机环境封装 | DualRelativeFrame, DualRelativeTargetFrame | - | gymnasium, numpy, rlinf, scipy |
| `rlinf/envs/realworld/common/wrappers/dual_spacemouse_intervention.py` | 99 | 仿真、benchmark、真机环境封装 | DualSpacemouseIntervention | - | __future__, gymnasium, numpy, rlinf, time |
| `rlinf/envs/realworld/common/wrappers/euler_obs.py` | 39 | 仿真、benchmark、真机环境封装 | Quat2EulerWrapper | - | gymnasium, numpy, scipy |
| `rlinf/envs/realworld/common/wrappers/gello_intervention.py` | 89 | 仿真、benchmark、真机环境封装 | GelloIntervention | - | gymnasium, numpy, rlinf, scipy, time |
| `rlinf/envs/realworld/common/wrappers/gripper_close.py` | 41 | 仿真、benchmark、真机环境封装 | GripperCloseEnv | - | gymnasium, numpy |
| `rlinf/envs/realworld/common/wrappers/leader_follower_keyboard_intervention.py` | 139 | 仿真、benchmark、真机环境封装 | LeaderFollowerKeyboardIntervention | - | __future__, gymnasium |
| `rlinf/envs/realworld/common/wrappers/relative_frame.py` | 141 | 仿真、benchmark、真机环境封装 | RelativeFrame, RelativeTargetFrame | - | gymnasium, numpy, rlinf, scipy |
| `rlinf/envs/realworld/common/wrappers/reward_done_wrapper.py` | 107 | 仿真、benchmark、真机环境封装；奖励计算或奖励模型 | BaseKeyboardRewardDoneWrapper, KeyboardRewardDoneWrapper, KeyboardRewardDoneMultiStageWrapper | - | gymnasium, rlinf, typing |
| `rlinf/envs/realworld/common/wrappers/spacemouse_intervention.py` | 88 | 仿真、benchmark、真机环境封装 | SpacemouseIntervention | sample_gripper_action | gymnasium, numpy, rlinf, time |
| `rlinf/envs/realworld/dosw1/__init__.py` | 17 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | rlinf |
| `rlinf/envs/realworld/dosw1/dosw1_env.py` | 692 | 仿真、benchmark、真机环境封装；环境适配 | ControlMode, DOSW1Config, DOSW1Env | - | __future__, copy, cv2, dataclasses, dosw1_robot_state, dosw1_sdk, enum, gymnasium |
| `rlinf/envs/realworld/dosw1/dosw1_robot_state.py` | 41 | 仿真、benchmark、真机环境封装 | DOSW1RobotState | - | dataclasses, numpy, time |
| `rlinf/envs/realworld/dosw1/dosw1_sdk.py` | 296 | 仿真、benchmark、真机环境封装 | DOSW1SDKAdapter | - | __future__, dosw1_robot_state, numpy, rlinf, time, typing |
| `rlinf/envs/realworld/dosw1/tasks/__init__.py` | 59 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | _maybe_apply_keyboard_intervention, create_dosw1_pick_env | __future__, gymnasium, rlinf, typing |
| `rlinf/envs/realworld/dosw1/tasks/pick.py` | 169 | 仿真、benchmark、真机环境封装 | PickConfig, PickEnv | _default_grasp_joint, _default_lift_joint | dataclasses, numpy, rlinf, time |
| `rlinf/envs/realworld/franka/__init__.py` | 24 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | end_effectors, franka_env |
| `rlinf/envs/realworld/franka/dual_franka_env.py` | 695 | 仿真、benchmark、真机环境封装；环境适配 | DualFrankaRobotConfig, DualFrankaEnv | - | __future__, copy, cv2, dataclasses, franka_robot_state, gymnasium, itertools, numpy |
| `rlinf/envs/realworld/franka/end_effectors/__init__.py` | 54 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | create_end_effector | base |
| `rlinf/envs/realworld/franka/end_effectors/base.py` | 167 | 仿真、benchmark、真机环境封装 | EndEffectorType, EndEffector | normalize_end_effector_type | abc, enum, numpy |
| `rlinf/envs/realworld/franka/end_effectors/franka_gripper.py` | 17 | 仿真、benchmark、真机环境封装 | - | - | rlinf |
| `rlinf/envs/realworld/franka/end_effectors/ruiyan_hand.py` | 17 | 仿真、benchmark、真机环境封装 | - | - | rlinf |
| `rlinf/envs/realworld/franka/franka_controller.py` | 405 | 仿真、benchmark、真机环境封装 | FrankaController | - | end_effectors, franka_robot_state, numpy, psutil, rlinf, scipy, sys, time |
| `rlinf/envs/realworld/franka/franka_env.py` | 927 | 仿真、benchmark、真机环境封装；环境适配 | FrankaRobotConfig, FrankaEnv | - | copy, cv2, dataclasses, end_effectors, franka_robot_state, gymnasium, itertools, numpy |
| `rlinf/envs/realworld/franka/franka_robot_state.py` | 62 | 仿真、benchmark、真机环境封装 | FrankaRobotState | - | dataclasses, numpy, typing |
| `rlinf/envs/realworld/franka/tasks/__init__.py` | 164 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | create_franka_env, create_dual_franka_env, create_peg_insertion_env, create_franka_bin_relocation_env, create_bottle_env, create_dexpnp_env | __future__, gymnasium, rlinf, typing |
| `rlinf/envs/realworld/franka/tasks/bottle.py` | 133 | 仿真、benchmark、真机环境封装 | BottleConfig, BottleEnv | - | copy, dataclasses, franka_env, numpy, time |
| `rlinf/envs/realworld/franka/tasks/dex_pnp.py` | 120 | 仿真、benchmark、真机环境封装 | DexpnpConfig, DexpnpEnv | - | copy, dataclasses, franka_env, numpy, time |
| `rlinf/envs/realworld/franka/tasks/franka_bin_relocation.py` | 241 | 仿真、benchmark、真机环境封装 | BinEnvConfig, FrankaBinRelocationEnv | - | copy, cv2, dataclasses, franka_env, gymnasium, numpy, queue, time |
| `rlinf/envs/realworld/franka/tasks/peg_insertion_env.py` | 126 | 仿真、benchmark、真机环境封装；环境适配 | PegInsertionConfig, PegInsertionEnv | - | copy, dataclasses, franka_env, numpy |
| `rlinf/envs/realworld/franka/utils.py` | 136 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | normalize, wrap_to_pi, clip_euler_to_target_window, quat_slerp, construct_adjoint_matrix, construct_homogeneous_matrix | numpy, scipy |
| `rlinf/envs/realworld/gim_arm/__init__.py` | 18 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | gim_arm_env, gim_arm_robot_state |
| `rlinf/envs/realworld/gim_arm/gim_arm_controller.py` | 335 | 仿真、benchmark、真机环境封装 | GimArmController | _smoothstep | gim_arm_robot_state, numpy, rlinf, threading, time |
| `rlinf/envs/realworld/gim_arm/gim_arm_env.py` | 526 | 仿真、benchmark、真机环境封装；环境适配 | GimArmRobotConfig, GimArmEnv | - | copy, cv2, dataclasses, gim_arm_robot_state, gymnasium, itertools, numpy, queue |
| `rlinf/envs/realworld/gim_arm/gim_arm_robot_state.py` | 63 | 仿真、benchmark、真机环境封装 | GimArmRobotState | - | dataclasses, numpy |
| `rlinf/envs/realworld/gim_arm/tasks/__init__.py` | 24 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | gymnasium, rlinf |
| `rlinf/envs/realworld/gim_arm/tasks/peg_insertion.py` | 140 | 仿真、benchmark、真机环境封装 | GimArmPegInsertionConfig, GimArmPegInsertionEnv | - | dataclasses, gim_arm_env, numpy, time |
| `rlinf/envs/realworld/realworld_env.py` | 402 | 仿真、benchmark、真机环境封装；环境适配 | RealWorldEnv | - | copy, filelock, functools, gymnasium, numpy, omegaconf, os, pathlib |
| `rlinf/envs/realworld/venv.py` | 319 | 仿真、benchmark、真机环境封装；环境适配 | NoAutoResetSyncVectorEnv, NoAutoResetAsyncVectorEnv | _worker_no_auto_reset, _worker_shared_memory_no_auto_reset | copy, gymnasium, multiprocessing, numpy, sys, typing |
| `rlinf/envs/realworld/xsquare/__init__.py` | 18 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | turtle2_env |
| `rlinf/envs/realworld/xsquare/tasks/__init__.py` | 47 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | create_button_env | __future__, gymnasium, rlinf, typing |
| `rlinf/envs/realworld/xsquare/tasks/button_env.py` | 82 | 仿真、benchmark、真机环境封装；环境适配 | ButtonEnvConfig, ButtonEnv | - | dataclasses, numpy, rlinf |
| `rlinf/envs/realworld/xsquare/turtle2_env.py` | 567 | 仿真、benchmark、真机环境封装；环境适配 | Turtle2RobotConfig, Turtle2Env | - | __future__, copy, cv2, dataclasses, gymnasium, numpy, rlinf, scipy |
| `rlinf/envs/realworld/xsquare/turtle2_robot_state.py` | 49 | 仿真、benchmark、真机环境封装 | Turtle2RobotState | - | dataclasses, numpy |
| `rlinf/envs/realworld/xsquare/turtle2_smooth_controller.py` | 264 | 仿真、benchmark、真机环境封装 | Turtle2SmoothController | - | cv_bridge, numpy, rlinf, rospy, time, tracemalloc, turtle2_basic, turtle2_robot_state |
| `rlinf/envs/robocasa/__init__.py` | 17 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | rlinf |
| `rlinf/envs/robocasa/robocasa_env.py` | 500 | 仿真、benchmark、真机环境封装；环境适配 | RobocasaEnv | - | copy, gymnasium, numpy, omegaconf, rlinf, torch, typing |
| `rlinf/envs/robocasa/utils.py` | 355 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | get_state_space, _check_state_space, get_state_ids, get_image_space, _check_image_space, get_action_space, _check_action_space, get_action_ids, tile_images, put_text_on_image | PIL, imageio, logging, numpy, os, torch, typing |
| `rlinf/envs/robocasa/venv.py` | 189 | 仿真、benchmark、真机环境封装；环境适配 | RobocasaSubprocEnvWorker, RobocasaSubprocEnv | _worker | gymnasium, multiprocessing, numpy, rlinf, typing |
| `rlinf/envs/robotwin/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/robotwin/robotwin_env.py` | 506 | 仿真、benchmark、真机环境封装；环境适配 | RoboTwinEnv | - | PIL, gymnasium, json, numpy, omegaconf, os, rlinf, torch |
| `rlinf/envs/roboverse/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/roboverse/roboverse_env.py` | 557 | 仿真、benchmark、真机环境封装；环境适配 | RoboVerseEnv | - | copy, gym, metasim, numpy, rlinf, torch, typing |
| `rlinf/envs/roboverse/utils.py` | 545 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | infer_state_count, slice_state_tree, select_initial_states, get_valid_joint_names, cfg_get, build_roboverse_camera_cfgs, resolve_camera_rgb, build_policy_states, extract_roboverse_obs, apply_action_guard | __future__, copy, metasim, numpy, pytorch3d, rlinf, torch, typing |
| `rlinf/envs/utils.py` | 337 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | to_tensor, recursive_to_device, list_of_dict_to_dict_of_list, save_rollout_video, tile_images, put_text_on_image, put_info_on_image, crop_and_resize, center_crop_image | PIL, numpy, os, torch, typing |
| `rlinf/envs/venv/__init__.py` | 33 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | venv |
| `rlinf/envs/venv/venv.py` | 985 | 仿真、benchmark、真机环境封装；环境适配 | CloudpickleWrapper, EnvWorker, ShArray, DummyEnvWorker, SubprocEnvWorker, BaseVectorEnv, DummyVectorEnv, SubprocVectorEnv | deprecation, _setup_buf, _worker | abc, cloudpickle, collections, ctypes, gym, multiprocessing, numpy, time |
| `rlinf/envs/world_model/__init__.py` | 13 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | - |
| `rlinf/envs/world_model/base_world_env.py` | 158 | 仿真、benchmark、真机环境封装；环境适配 | BaseWorldEnv | - | __future__, abc, rlinf, torch, typing |
| `rlinf/envs/world_model/world_model_opensora_env.py` | 917 | 仿真、benchmark、真机环境封装；环境适配 | OpenSoraEnv | - | collections, io, json, numpy, omegaconf, opensora, os, rlinf |
| `rlinf/envs/world_model/world_model_wan_env.py` | 844 | 仿真、benchmark、真机环境封装；环境适配 | WanEnv | - | PIL, diffsynth, io, numpy, os, pathlib, rlinf, torch |
| `rlinf/envs/wrappers/__init__.py` | 18 | 仿真、benchmark、真机环境封装；公共入口/工具 | - | - | rlinf |
| `rlinf/envs/wrappers/collect_episode.py` | 804 | 仿真、benchmark、真机环境封装 | CollectEpisode | - | __future__, atexit, concurrent, copy, gymnasium, numpy, os, pickle |
| `rlinf/envs/wrappers/record_video.py` | 487 | 仿真、benchmark、真机环境封装 | RecordVideo | - | concurrent, gymnasium, imageio, numbers, numpy, os, rlinf, typing |
