"""4.1 - Coordinate-frame transform demo.

Show how a 3D point expressed in the camera frame is converted into the
robot base frame using a fixed extrinsic transform.

Run:
    python labs/04-perception/coordinate_frame_demo.py
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

np.set_printoptions(precision=4, suppress=True, sign=" ")


RUN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "runs", "05-perception")
)
os.makedirs(RUN_DIR, exist_ok=True)


def rot_xyz(rx: float, ry: float, rz: float) -> np.ndarray:
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    rx_m = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry_m = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz_m = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz_m @ ry_m @ rx_m


def make_transform(r: np.ndarray, t: np.ndarray) -> np.ndarray:
    transform = np.eye(4)
    transform[:3, :3] = r
    transform[:3, 3] = t
    return transform


def invert_transform(transform: np.ndarray) -> np.ndarray:
    rotation = transform[:3, :3]
    translation = transform[:3, 3]
    inv = np.eye(4)
    inv[:3, :3] = rotation.T
    inv[:3, 3] = -rotation.T @ translation
    return inv


def transform_point(transform: np.ndarray, point_xyz: np.ndarray) -> np.ndarray:
    point_h = np.concatenate([point_xyz, np.array([1.0])])
    out_h = transform @ point_h
    return out_h[:3]


def main() -> None:
    r_base_camera = rot_xyz(
        math.radians(-8.0),
        math.radians(14.0),
        math.radians(18.0),
    )
    t_base_camera = np.array([0.42, -0.18, 0.72])
    t_base_camera_m = make_transform(r_base_camera, t_base_camera)

    point_camera = np.array([0.08, -0.03, 0.55])
    point_base = transform_point(t_base_camera_m, point_camera)
    point_camera_roundtrip = transform_point(
        invert_transform(t_base_camera_m),
        point_base,
    )
    roundtrip_err_mm = float(np.linalg.norm(point_camera_roundtrip - point_camera) * 1000.0)

    print("--- fixed extrinsic: T_base_camera ---")
    print(t_base_camera_m)
    print("\npoint in camera frame =", point_camera, "(metres)")
    print("point in base frame   =", point_base, "(metres)")
    print(f"round-trip error      = {roundtrip_err_mm:.6f} mm")

    payload = {
        "frame_graph": {
            "target_frame": "robot_base",
            "source_frame": "wrist_color_optical_frame",
        },
        "transform": {
            "T_base_camera": t_base_camera_m.round(6).tolist(),
        },
        "point_camera_xyz_m": point_camera.round(6).tolist(),
        "point_base_xyz_m": point_base.round(6).tolist(),
        "roundtrip_error_mm": round(roundtrip_err_mm, 6),
    }

    out_path = os.path.join(RUN_DIR, "coordinate_frame_demo.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"wrote {out_path}")

    assert roundtrip_err_mm < 1e-6, "frame transform round-trip error is not near zero"
    print(">>> PASS: camera-frame point mapped to base frame and back consistently.")


if __name__ == "__main__":
    main()
