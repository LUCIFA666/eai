# SimpleVLA-RL 文件索引：robotwin2-mods

覆盖 `robotwin2-mods` 分组，共 `31` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `modified_codes/robotwin2/description/utils/generate_episode_instructions.py` | 326 | RoboTwin2 环境改造代码 | - | extract_placeholders, filter_instructions, replace_placeholders, replace_placeholders_unseen, load_task_instructions, load_scene_info, extract_episodes_from_scene_info, save_episode_descriptions, generate_episode_descriptions | argparse, json, os, pdb, random, re, typing, yaml |
| `modified_codes/robotwin2/envs/_base_task.py` | 1902 | RoboTwin2 环境改造代码 | Base_Task | - | _GLOBAL_CONFIGS, camera, collections, copy, glob, gymnasium, imageio, json |
| `modified_codes/robotwin2/envs/beat_block_hammer.py` | 93 | RoboTwin2 环境改造代码 | beat_block_hammer | - | _GLOBAL_CONFIGS, _base_task, sapien, utils |
| `modified_codes/robotwin2/envs/blocks_ranking_rgb.py` | 181 | RoboTwin2 环境改造代码 | blocks_ranking_rgb | - | _base_task, math, numpy, sapien, utils |
| `modified_codes/robotwin2/envs/click_bell.py` | 87 | RoboTwin2 环境改造代码 | click_bell | - | _base_task, copy, math, sapien, utils |
| `modified_codes/robotwin2/envs/handover_block.py` | 119 | RoboTwin2 环境改造代码 | handover_block | - | _GLOBAL_CONFIGS, _base_task, math, sapien, utils |
| `modified_codes/robotwin2/envs/handover_mic.py` | 121 | RoboTwin2 环境改造代码 | handover_mic | - | _GLOBAL_CONFIGS, _base_task, utils |
| `modified_codes/robotwin2/envs/lift_pot.py` | 62 | RoboTwin2 环境改造代码 | lift_pot | - | _base_task, math, sapien, utils |
| `modified_codes/robotwin2/envs/move_can_pot.py` | 119 | RoboTwin2 环境改造代码 | move_can_pot | - | _base_task, copy, math, sapien, utils |
| `modified_codes/robotwin2/envs/move_pillbottle_pad.py` | 111 | RoboTwin2 环境改造代码 | move_pillbottle_pad | - | _GLOBAL_CONFIGS, _base_task, copy, math, sapien, utils |
| `modified_codes/robotwin2/envs/move_stapler_pad.py` | 129 | RoboTwin2 环境改造代码 | move_stapler_pad | - | _GLOBAL_CONFIGS, _base_task, copy, math, sapien, utils |
| `modified_codes/robotwin2/envs/pick_dual_bottles.py` | 106 | RoboTwin2 环境改造代码 | pick_dual_bottles | - | _base_task, copy, sapien, utils |
| `modified_codes/robotwin2/envs/place_a2b_left.py` | 163 | RoboTwin2 环境改造代码 | place_a2b_left | - | _GLOBAL_CONFIGS, _base_task, copy, glob, math, numpy, os, sapien |
| `modified_codes/robotwin2/envs/place_a2b_right.py` | 164 | RoboTwin2 环境改造代码 | place_a2b_right | - | _GLOBAL_CONFIGS, _base_task, copy, glob, math, numpy, os, sapien |
| `modified_codes/robotwin2/envs/place_container_plate.py` | 108 | RoboTwin2 环境改造代码 | place_container_plate | - | _base_task, sapien, utils |
| `modified_codes/robotwin2/envs/place_empty_cup.py` | 101 | RoboTwin2 环境改造代码 | place_empty_cup | - | _base_task, sapien, utils |
| `modified_codes/robotwin2/envs/place_mouse_pad.py` | 137 | RoboTwin2 环境改造代码 | place_mouse_pad | - | _GLOBAL_CONFIGS, _base_task, copy, math, numpy, sapien, utils |
| `modified_codes/robotwin2/envs/place_phone_stand.py` | 113 | RoboTwin2 环境改造代码 | place_phone_stand | - | _base_task, copy, sapien, utils |
| `modified_codes/robotwin2/envs/place_shoe.py` | 106 | RoboTwin2 环境改造代码 | place_shoe | - | _base_task, math, sapien, utils |
| `modified_codes/robotwin2/envs/put_bottles_dustbin.py` | 162 | RoboTwin2 环境改造代码 | put_bottles_dustbin | - | _base_task, copy, sapien, utils |
| `modified_codes/robotwin2/envs/robot/planner.py` | 544 | RoboTwin2 环境改造代码 | MplibPlanner | - | envs, mplib, numpy, os, pdb, sapien, toppra, traceback |
| `modified_codes/robotwin2/envs/robot/planner_curobo.py` | 434 | RoboTwin2 环境改造代码 | MplibPlanner | - | envs, mplib, numpy, pdb, toppra, traceback, transforms3d |
| `modified_codes/robotwin2/envs/robot/robot.py` | 737 | RoboTwin2 环境改造代码 | Robot | planner_process_worker | copy, envs, math, numpy, os, pdb, planner, sapien |
| `modified_codes/robotwin2/envs/robot/robot_curobo.py` | 714 | RoboTwin2 环境改造代码 | Robot | planner_process_worker | copy, envs, math, numpy, os, pdb, planner, sapien |
| `modified_codes/robotwin2/envs/shake_bottle.py` | 92 | RoboTwin2 环境改造代码 | shake_bottle | - | _base_task, math, sapien, utils |
| `modified_codes/robotwin2/envs/stack_blocks_two.py` | 141 | RoboTwin2 环境改造代码 | stack_blocks_two | - | _base_task, math, sapien, utils |
| `modified_codes/robotwin2/envs/stack_bowls_two.py` | 143 | RoboTwin2 环境改造代码 | stack_bowls_two | - | _base_task, math, sapien, utils |
| `modified_codes/robotwin2/envs/utils/create_actor.py` | 653 | RoboTwin2 环境改造代码；策略/actor 逻辑 | UnStableError | preprocess, create_entity_box, create_box, create_sphere, create_cylinder, create_visual_box, create_table, create_obj, create_glb, get_glb_or_obj_file | actor_utils, json, numpy, os, pathlib, re, sapien, transforms3d |
| `modified_codes/robotwin2/envs/utils/rand_create_cluttered_actor.py` | 285 | RoboTwin2 环境改造代码；策略/actor 逻辑 | - | get_all_cluttered_objects, get_available_cluttered_objects, check_overlap, rand_pose_cluttered, rand_create_cluttered_actor, create_cluttered_urdf_obj | create_actor, json, numpy, os, pathlib, re, sapien, transforms3d |
| `modified_codes/robotwin2/envs/utils/transforms.py` | 534 | RoboTwin2 环境改造代码 | Point | pause, timer, local_timer, rotate_cone, _tolist, _toPose, rotate_along_axis, rotate2rob, choose_dirct, add_robot_visual_box | functools, numpy, os, pathlib, sapien, time, transforms3d, typing |
| `modified_codes/robotwin2/script/update_embodiment_config_path.py` | 141 | RoboTwin2 环境改造代码；配置/参数定义 | - | print_color, prompt_path, main | glob, os, sys |
