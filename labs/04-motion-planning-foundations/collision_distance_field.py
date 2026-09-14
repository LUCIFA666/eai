"""2-D occupancy/SDF demo used by section 4.1.1.

The robot is simplified to a disc and the path to a polyline.  This is not a
robot-arm collision checker; it isolates the three ideas that matter later:
occupancy, signed clearance, and checking the whole path instead of endpoints.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import distance_transform_edt


def build_occupancy(size: int = 220) -> np.ndarray:
    occupancy = np.zeros((size, size), dtype=bool)
    occupancy[70:155, 92:122] = True
    yy, xx = np.mgrid[:size, :size]
    occupancy |= (xx - 166) ** 2 + (yy - 70) ** 2 <= 24**2
    return occupancy


def signed_distance(occupancy: np.ndarray, resolution: float) -> np.ndarray:
    outside = distance_transform_edt(~occupancy) * resolution
    inside = distance_transform_edt(occupancy) * resolution
    return outside - inside


def sample_polyline(waypoints: np.ndarray, samples_per_segment: int) -> np.ndarray:
    samples: list[np.ndarray] = []
    for start, goal in zip(waypoints[:-1], waypoints[1:]):
        alpha = np.linspace(0.0, 1.0, samples_per_segment, endpoint=False)[:, None]
        samples.append((1.0 - alpha) * start + alpha * goal)
    samples.append(waypoints[-1:])
    return np.concatenate(samples, axis=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("collision_clearance.png"))
    parser.add_argument("--samples-per-segment", type=int, default=120)
    parser.add_argument("--robot-radius", type=float, default=0.09)
    args = parser.parse_args()

    resolution = 0.01  # metres per grid cell
    occupancy = build_occupancy()
    sdf = signed_distance(occupancy, resolution)

    # x/y are expressed in metres.  The middle waypoint deliberately bends
    # around the rectangular obstacle.
    waypoints = np.array([[0.20, 0.25], [0.78, 1.78], [2.02, 1.86]])
    path = sample_polyline(waypoints, args.samples_per_segment)
    ij = np.rint(path[:, ::-1] / resolution).astype(int)
    ij[:, 0] = np.clip(ij[:, 0], 0, sdf.shape[0] - 1)
    ij[:, 1] = np.clip(ij[:, 1], 0, sdf.shape[1] - 1)

    clearance = sdf[ij[:, 0], ij[:, 1]] - args.robot_radius
    min_index = int(np.argmin(clearance))
    print(f"samples={len(path)}")
    print(f"minimum_clearance_m={clearance[min_index]:.4f}")
    print(f"collision={bool(np.any(clearance <= 0.0))}")

    extent = [0.0, occupancy.shape[1] * resolution, 0.0, occupancy.shape[0] * resolution]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), constrained_layout=True)
    axes[0].imshow(occupancy, origin="lower", extent=extent, cmap="gray_r")
    axes[0].plot(path[:, 0], path[:, 1], color="#12a594", linewidth=3)
    axes[0].scatter(*path[min_index], color="#ef8354", s=55, zorder=5)
    axes[0].set_title("Occupancy + sampled path")
    axes[0].set_aspect("equal")

    image = axes[1].imshow(sdf, origin="lower", extent=extent, cmap="coolwarm", vmin=-0.35, vmax=0.35)
    axes[1].contour(
        np.arange(sdf.shape[1]) * resolution,
        np.arange(sdf.shape[0]) * resolution,
        sdf,
        levels=[args.robot_radius],
        colors=["#172a3a"],
        linewidths=1.5,
    )
    axes[1].plot(path[:, 0], path[:, 1], color="#12a594", linewidth=3)
    axes[1].set_title("Signed distance field")
    axes[1].set_aspect("equal")
    fig.colorbar(image, ax=axes[1], label="signed distance [m]")
    for axis in axes:
        axis.set_xlabel("x [m]")
        axis.set_ylabel("y [m]")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=170)
    print(f"saved={args.output.resolve()}")


if __name__ == "__main__":
    main()
