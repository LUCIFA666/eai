"""4.2 — Project a synthetic RGB-D frame to a point cloud.

We render a procedural scene of three coloured boxes sitting on a table.
The "depth" buffer is computed analytically from the box geometry so we
do not depend on a renderer.  The script then back-projects every valid
depth pixel using the pinhole equation::

    X = (u - cx) * Z / fx
    Y = (v - cy) * Z / fy
    Z = depth[v, u]

and saves a coloured point cloud as a binary-less ASCII PLY plus a PNG
preview of the depth image.  If Open3D is installed we additionally save
``.pcd`` and let users open it interactively, but the script runs fine
without it.

Run:
    python labs/04-perception/rgbd_to_pointcloud.py
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass

import cv2
import numpy as np

np.set_printoptions(precision=4, suppress=True)


W, H = 640, 480
FX = FY = 525.0           # Kinect-v1 default focal length
CX, CY = W / 2.0, H / 2.0
DEPTH_TRUNC = 4.0          # metres
TABLE_HEIGHT_Z = 0.75      # camera 0.75 m above the table
RUN_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "runs", "05-perception")
RUN_DIR = os.path.abspath(RUN_DIR)


@dataclass
class Box:
    cx: float          # box centre x in world coords (camera looks down at +z)
    cy: float
    size: tuple[float, float, float]
    color: tuple[int, int, int]   # RGB 0-255


def render_scene():
    """Return ``(rgb, depth)`` arrays for a scene seen from above the table.

    World convention used here: camera origin at ``(0, 0, 0)`` looking
    down +Z; X to the right, Y down (matches OpenCV image axes).  The
    table is a flat plane at ``Z = TABLE_HEIGHT_Z``.
    """
    depth = np.full((H, W), TABLE_HEIGHT_Z, dtype=np.float32)
    rgb = np.zeros((H, W, 3), dtype=np.uint8)

    # Paint table colour for every pixel.
    rgb[:, :] = (170, 150, 130)

    boxes = [
        Box(cx=-0.10, cy=-0.05, size=(0.10, 0.10, 0.12), color=(220, 70, 70)),
        Box(cx=0.08, cy=0.04, size=(0.06, 0.08, 0.18), color=(70, 180, 90)),
        Box(cx=0.00, cy=0.13, size=(0.12, 0.06, 0.05), color=(70, 90, 220)),
    ]

    # For every pixel cast a ray and find the closest hit.
    us = np.arange(W)
    vs = np.arange(H)[:, None]
    rays_x = (us - CX) / FX
    rays_y = (vs - CY) / FY

    for box in boxes:
        top_z = TABLE_HEIGHT_Z - box.size[2]  # box top closer to camera than table
        # parametrise the top face: it sits at z = top_z.
        z_hit = top_z
        # solve for (x, y) on the plane: x = rays_x * z, y = rays_y * z
        x = rays_x * z_hit
        y = rays_y * z_hit
        mask = (
            (x >= box.cx - box.size[0] / 2)
            & (x <= box.cx + box.size[0] / 2)
            & (y >= box.cy - box.size[1] / 2)
            & (y <= box.cy + box.size[1] / 2)
            & (z_hit < depth)
        )
        depth[mask] = z_hit
        rgb[mask] = box.color

    # Add a couple of depth holes near the green box to mimic specular drop-out.
    holes = np.zeros_like(depth, dtype=bool)
    holes[120:140, 350:380] = True
    holes[210:225, 360:395] = True
    depth[holes] = 0.0

    return rgb, depth


def depth_to_pointcloud(rgb: np.ndarray, depth: np.ndarray):
    valid = (depth > 0) & (depth < DEPTH_TRUNC)
    us, vs = np.meshgrid(np.arange(W), np.arange(H))
    u = us[valid].astype(np.float32)
    v = vs[valid].astype(np.float32)
    z = depth[valid].astype(np.float32)
    x = (u - CX) * z / FX
    y = (v - CY) * z / FY
    xyz = np.stack([x, y, z], axis=1)
    rgb_pts = rgb[valid]
    return xyz, rgb_pts, valid.sum()


def write_ply(path: str, xyz: np.ndarray, rgb: np.ndarray) -> None:
    n = xyz.shape[0]
    with open(path, "w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {n}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("end_header\n")
        for (x, y, z), (r, g, b) in zip(xyz, rgb):
            f.write(f"{x:.5f} {y:.5f} {z:.5f} {int(r)} {int(g)} {int(b)}\n")


def write_depth_png(path: str, depth: np.ndarray) -> None:
    """Save depth as a 16-bit PNG (mm), like OpenNI / TUM datasets."""
    depth_mm = np.where(depth > 0, np.clip(depth * 1000.0, 0, 65535), 0).astype(np.uint16)
    cv2.imwrite(path, depth_mm)


def main() -> None:
    os.makedirs(RUN_DIR, exist_ok=True)
    rgb, depth = render_scene()
    xyz, rgb_pts, n_valid = depth_to_pointcloud(rgb, depth)

    ply_path = os.path.join(RUN_DIR, "scene.ply")
    rgb_path = os.path.join(RUN_DIR, "scene_rgb.png")
    depth_path = os.path.join(RUN_DIR, "scene_depth_mm.png")
    write_ply(ply_path, xyz, rgb_pts)
    cv2.imwrite(rgb_path, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    write_depth_png(depth_path, depth)

    print(f"image size = {W}x{H}, fx={FX}, fy={FY}, cx={CX}, cy={CY}")
    print(f"depth range: {depth[depth>0].min():.3f} .. {depth.max():.3f} m")
    print(f"valid pixels = {n_valid:,} / {W*H:,} ({100.0*n_valid/(W*H):.2f}%)")
    print(f"point cloud xyz bounds  min = {xyz.min(axis=0)}")
    print(f"point cloud xyz bounds  max = {xyz.max(axis=0)}")
    print(f"wrote {ply_path}")
    print(f"wrote {rgb_path}")
    print(f"wrote {depth_path}")

    # ------------------------------------------------------------------
    # Sanity round-trip: re-project the point cloud back to pixels and
    # compare against the originals.  Should match within 1e-4 px because
    # we used analytic geometry.
    # ------------------------------------------------------------------
    rng = np.random.default_rng(0)
    idx = rng.choice(xyz.shape[0], size=100, replace=False)
    sample = xyz[idx]
    u_back = sample[:, 0] * FX / sample[:, 2] + CX
    v_back = sample[:, 1] * FY / sample[:, 2] + CY
    # Compare with stored pixel grid.
    us, vs = np.meshgrid(np.arange(W), np.arange(H))
    valid = (depth > 0) & (depth < DEPTH_TRUNC)
    u_true = us[valid][idx]
    v_true = vs[valid][idx]
    err = np.max(np.hypot(u_back - u_true, v_back - v_true))
    print(f"reprojection round-trip max error = {err:.2e} px")

    try:
        import open3d as o3d  # noqa: F401
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64))
        pcd.colors = o3d.utility.Vector3dVector(rgb_pts.astype(np.float64) / 255.0)
        pcd_path = os.path.join(RUN_DIR, "scene.pcd")
        o3d.io.write_point_cloud(pcd_path, pcd)
        print(f"wrote {pcd_path} (open3d available)")
    except Exception as exc:
        print(f"open3d unavailable, skipped .pcd export ({exc.__class__.__name__})")


if __name__ == "__main__":
    main()
