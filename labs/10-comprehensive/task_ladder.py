"""10.1 — Sanity check: list the task difficulty ladder.

This is a *pure-Python* helper that prints the canonical task ladder
for embodied AI (PointNav → ObjectNav → PickPlace → language PickPlace
→ mobile manipulation → OVMM), along with their benchmarks, eval
protocols, and dataset prerequisites.  No model is loaded.

We use it both as a learning aid (run it to see the table) and as a
machine-checkable spec — chapter 10 sub-pages embed the same table
from the JSON written here.

Run:
    python labs/10-comprehensive/task_ladder.py

Outputs:
- prints a markdown-style ladder
- writes ``runs/10-comprehensive/task_ladder.json``
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path("runs/10-comprehensive/task_ladder.json")

LADDER = [
    {
        "level": 1,
        "task": "PointNav",
        "description": "导航到 (Δx, Δy) 给定的目标点",
        "obs": ["rgb", "depth", "gps", "compass"],
        "action": "discrete (forward/left/right/stop)",
        "benchmarks": ["Habitat PointNav v1/v2", "Gibson"],
        "metric": "Success, SPL",
        "dataset": "HM3D, Matterport3D",
        "typical_baseline_success": "PPO 30M steps ≈ 80%",
    },
    {
        "level": 2,
        "task": "ObjectNav",
        "description": "导航到 «沙发 / 床 / 椅子» 等语义类别",
        "obs": ["rgb", "depth", "category"],
        "action": "discrete (forward/left/right/stop)",
        "benchmarks": ["Habitat ObjectNav 2022/2023"],
        "metric": "Success, SPL",
        "dataset": "HM3D-Semantics, Gibson",
        "typical_baseline_success": "PPO + ImageNav 30M ≈ 35-40%",
    },
    {
        "level": 3,
        "task": "Tabletop PickPlace",
        "description": "从桌面抓取一个物体放到目标位置",
        "obs": ["rgb", "depth", "joint_state"],
        "action": "continuous (delta EE pose, 7D)",
        "benchmarks": ["ManiSkill PickCube", "robomimic Lift/Can"],
        "metric": "Success",
        "dataset": "demonstration data (200-2000 demos)",
        "typical_baseline_success": "BC + Diffusion Policy 80-95%",
    },
    {
        "level": 4,
        "task": "Language-conditioned PickPlace",
        "description": "«把红方块放到蓝盘子里» 等模板指令",
        "obs": ["rgb", "depth", "joint_state", "instruction"],
        "action": "continuous + language",
        "benchmarks": ["LIBERO (4 suites)", "CALVIN", "Meta-World ML10/45"],
        "metric": "Success per task / suite",
        "dataset": "LIBERO 4*10*50 demos; CALVIN 6h play data",
        "typical_baseline_success": "OpenVLA 75-85%, π0.5 95%+",
    },
    {
        "level": 5,
        "task": "Mobile Manipulation",
        "description": "在家庭场景中导航 + 操作",
        "obs": ["multi-view rgb", "depth", "base pose", "ee pose"],
        "action": "base velocity + arm pose + gripper",
        "benchmarks": ["Habitat Rearrangement", "ManiSkill 3 Mobile"],
        "metric": "Sub-task success rates",
        "dataset": "scripted + RL fine-tune",
        "typical_baseline_success": "末端组合 30-50%",
    },
    {
        "level": 6,
        "task": "Open-Vocabulary Mobile Manipulation (OVMM)",
        "description": "用文本指定任意目标物体类别 + 移动操作",
        "obs": ["multi-view rgb", "depth", "base pose", "instruction"],
        "action": "navigation + manipulation + skill switching",
        "benchmarks": ["HomeRobot OVMM Challenge", "BEHAVIOR-1K", "RoboCasa"],
        "metric": "Total success, partial success, sub-task SR",
        "dataset": "HSSD, HomeRobot training scenes",
        "typical_baseline_success": "HomeRobot baseline ~ 0-10% total",
    },
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"ladder": LADDER}, indent=2, ensure_ascii=False))

    print("# Embodied AI 任务难度阶梯\n")
    for row in LADDER:
        print(f"## L{row['level']}: {row['task']}")
        print(f"- 描述: {row['description']}")
        print(f"- obs: {', '.join(row['obs'])}")
        print(f"- action: {row['action']}")
        print(f"- benchmarks: {', '.join(row['benchmarks'])}")
        print(f"- 指标: {row['metric']}")
        print(f"- 数据: {row['dataset']}")
        print(f"- 典型 baseline: {row['typical_baseline_success']}")
        print()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
