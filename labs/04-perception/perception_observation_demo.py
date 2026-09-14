"""4.8 - Build a minimal perception observation and action suggestion.

Run:
    python labs/04-perception/perception_observation_demo.py
"""
from __future__ import annotations

import json
import os


RUN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "runs", "05-perception")
)
os.makedirs(RUN_DIR, exist_ok=True)


def choose_perception_action(confidence: float, failure_code: str | None, staleness_ms: int) -> str:
    if failure_code in {"frame_mismatch", "extrinsic_missing", "intrinsic_resolution_mismatch"}:
        return "abort"
    if failure_code in {"no_detection", "track_lost", "depth_inconsistent"}:
        return "reobserve"
    if staleness_ms > 120:
        return "refresh"
    if confidence < 0.70:
        return "degrade"
    return "execute"


def main() -> None:
    observation = {
        "schema_version": "perception_observation_v1",
        "timestamp": "2026-05-30T10:18:24.120Z",
        "frame_graph": {
            "world": "world",
            "robot_base": "panda_link0",
            "camera": "wrist_color_optical_frame",
            "gripper": "gripper_tcp",
        },
        "objects": [
            {
                "object_id": "mug_01",
                "label": "red mug",
                "bbox_xyxy": [412, 208, 610, 470],
                "pose": {
                    "frame_id": "panda_link0",
                    "xyz_m": [0.43, -0.12, 0.08],
                    "quat_xyzw": [0.0, 0.0, 0.71, 0.70],
                },
                "confidence": 0.84,
                "staleness_ms": 37,
                "failure_code": None,
            },
            {
                "object_id": "bowl_01",
                "label": "white bowl",
                "bbox_xyxy": [138, 190, 332, 411],
                "pose": {
                    "frame_id": "panda_link0",
                    "xyz_m": [0.31, 0.16, 0.07],
                    "quat_xyzw": [0.0, 0.0, 0.0, 1.0],
                },
                "confidence": 0.58,
                "staleness_ms": 24,
                "failure_code": "ambiguous_target",
            },
        ],
        "contacts": [
            {
                "event_type": "stable_grasp",
                "frame_id": "gripper_tcp",
                "force_norm_n": 4.8,
                "confidence": 0.81,
                "failure_code": None,
            }
        ],
    }

    suggestions = {}
    print(f"{'object_id':12s} {'confidence':>10s} {'staleness_ms':>13s} {'failure_code':>18s} {'action':>10s}")
    print("-" * 76)
    for obj in observation["objects"]:
        action = choose_perception_action(
            confidence=float(obj["confidence"]),
            failure_code=obj["failure_code"],
            staleness_ms=int(obj["staleness_ms"]),
        )
        suggestions[obj["object_id"]] = action
        print(
            f"{obj['object_id']:12s} {float(obj['confidence']):10.2f} "
            f"{int(obj['staleness_ms']):13d} {str(obj['failure_code']):>18s} {action:>10s}"
        )

    payload = {
        "observation": observation,
        "suggested_actions": suggestions,
    }
    out_path = os.path.join(RUN_DIR, "observation_demo.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\nwrote {out_path}")
    assert suggestions["mug_01"] == "execute"
    print(">>> PASS: observation was generated and action suggestions were derived.")


if __name__ == "__main__":
    main()
