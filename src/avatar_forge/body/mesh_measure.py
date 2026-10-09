from __future__ import annotations

from math import isfinite
from typing import Any

import numpy as np
import trimesh


def _polygon_area(coordinates: np.ndarray) -> float:
    x = coordinates[:, 0]
    y = coordinates[:, 1]
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2)


def _polygon_covers(coordinates: np.ndarray, point: np.ndarray) -> bool:
    vertices = coordinates[:-1]
    following = np.roll(vertices, -1, axis=0)
    x, y = point
    x1, y1 = vertices[:, 0], vertices[:, 1]
    x2, y2 = following[:, 0], following[:, 1]

    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    on_edge = (
        (np.abs(cross) <= 1e-8)
        & (x >= np.minimum(x1, x2) - 1e-8)
        & (x <= np.maximum(x1, x2) + 1e-8)
        & (y >= np.minimum(y1, y2) - 1e-8)
        & (y <= np.maximum(y1, y2) + 1e-8)
    )
    crossing = (y1 > y) != (y2 > y)
    intersections = x1 + (y - y1) * (x2 - x1) / np.where(
        y2 != y1, y2 - y1, 1.0
    )
    return bool(np.any(on_edge) or np.count_nonzero(crossing & (x < intersections)) % 2)


def _section_perimeter(
    mesh: trimesh.Trimesh, vertices: np.ndarray, axis: int, height_cm: float
) -> float:
    origin = np.zeros(3, dtype=np.float64)
    origin[axis] = height_cm
    section = mesh.section(plane_origin=origin, plane_normal=np.eye(3)[axis])
    if section is None:
        raise ValueError(f"Mesh has no closed section at {height_cm:.2f} cm")

    near_plane = np.abs(vertices[:, axis] - height_cm) <= 1.0
    centre_vertices = vertices[near_plane] if np.any(near_plane) else vertices
    planar_axes = [coordinate for coordinate in range(3) if coordinate != axis]
    centre = centre_vertices[:, planar_axes].mean(axis=0)

    loops: list[tuple[np.ndarray, float, float]] = []
    for coordinates in section.discrete:
        if len(coordinates) < 4 or not np.allclose(
            coordinates[0], coordinates[-1], atol=1e-5
        ):
            continue
        polygon = coordinates[:, planar_axes]
        area = _polygon_area(polygon)
        if area > 0:
            perimeter = float(np.linalg.norm(np.diff(polygon, axis=0), axis=1).sum())
            loops.append((polygon, area, perimeter))
    if not loops:
        raise ValueError(f"Mesh section at {height_cm:.2f} cm has no closed loops")

    torso_loops = [
        loop for loop in loops if _polygon_covers(loop[0], centre)
    ]
    selected = max(torso_loops or loops, key=lambda loop: loop[1])
    return selected[2]


def measure_mesh(
    vertices: np.ndarray, faces: np.ndarray, height_cm: float, cfg: dict[str, Any]
) -> dict[str, float]:
    """Measure torso circumferences by slicing a mesh scaled to the requested height."""
    source_vertices = np.asarray(vertices, dtype=np.float64)
    source_faces = np.asarray(faces, dtype=np.int64)
    if (
        source_vertices.ndim != 2
        or source_vertices.shape[1] != 3
        or len(source_vertices) < 3
        or not np.isfinite(source_vertices).all()
    ):
        raise ValueError("vertices must be a finite (N, 3) array")
    if (
        source_faces.ndim != 2
        or source_faces.shape[1] != 3
        or len(source_faces) == 0
        or source_faces.min() < 0
        or source_faces.max() >= len(source_vertices)
    ):
        raise ValueError("faces must be a non-empty (M, 3) array of valid indices")
    if not isfinite(height_cm) or height_cm <= 0:
        raise ValueError("height_cm must be a positive finite number")

    extents = np.ptp(source_vertices, axis=0)
    up_axis = int(np.argmax(extents))
    stature = float(extents[up_axis])
    if not isfinite(stature) or stature <= 0:
        raise ValueError("Mesh must have positive stature")

    scaled_vertices = source_vertices * (height_cm / stature)
    scaled_vertices[:, up_axis] -= float(source_vertices[:, up_axis].min()) * (
        height_cm / stature
    )
    mesh = trimesh.Trimesh(
        vertices=scaled_vertices, faces=source_faces, process=False
    )

    body_cfg = cfg.get("stages", {}).get("s04_body_fit", {})
    slice_cfg = body_cfg.get("mesh_slice", {})
    bust_fraction = float(slice_cfg["bust"])
    underbust_fraction = float(slice_cfg["underbust"])
    waist_range = slice_cfg["waist_range"]
    hips_range = slice_cfg["hips_range"]
    range_steps = int(slice_cfg["range_steps"])
    fractions = [bust_fraction, underbust_fraction, *waist_range, *hips_range]
    if (
        len(waist_range) != 2
        or len(hips_range) != 2
        or range_steps < 1
        or any(not isfinite(float(value)) or not 0 <= float(value) <= 1 for value in fractions)
        or waist_range[0] > waist_range[1]
        or hips_range[0] > hips_range[1]
    ):
        raise ValueError("mesh_slice fractions must be ordered values in [0, 1]")

    def circumference(fraction: float) -> float:
        return _section_perimeter(
            mesh, scaled_vertices, up_axis, fraction * height_cm
        )

    waist = [
        circumference(float(fraction))
        for fraction in np.linspace(waist_range[0], waist_range[1], range_steps)
    ]
    hips = [
        circumference(float(fraction))
        for fraction in np.linspace(hips_range[0], hips_range[1], range_steps)
    ]
    return {
        "height": float(height_cm),
        "bust": circumference(bust_fraction),
        "underbust": circumference(underbust_fraction),
        "waist": min(waist),
        "hips": max(hips),
    }
