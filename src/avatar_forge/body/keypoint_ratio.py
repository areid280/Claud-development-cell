from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import hypot, isfinite, pi, sqrt
from typing import Any

import numpy as np


def _point(keypoints: Mapping[str, Any], name: str) -> tuple[float, float]:
    value = keypoints.get(name)
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) < 2
    ):
        raise ValueError(f"Missing or invalid keypoint {name!r}")
    x, y = float(value[0]), float(value[1])
    if not isfinite(x) or not isfinite(y):
        raise ValueError(f"Keypoint {name!r} must contain finite coordinates")
    return x, y


def _mask(alpha: np.ndarray) -> np.ndarray:
    silhouette = np.asarray(alpha)
    if silhouette.ndim == 3:
        silhouette = (
            silhouette[:, :, -1]
            if silhouette.shape[2] == 4
            else silhouette.any(axis=2)
        )
    if silhouette.ndim != 2:
        raise ValueError("alpha must be a 2D mask or an image with 3 or 4 channels")
    return silhouette > 0


def _mask_above_head(
    keypoints: Mapping[str, Any],
    names: tuple[str, ...],
    head_y: float,
    shape: tuple[int, int],
) -> bool:
    for name in names:
        raw_mask = keypoints.get(name)
        if raw_mask is None:
            continue
        mask = np.asarray(raw_mask)
        if mask.shape != shape:
            raise ValueError(f"{name} has shape {mask.shape}; expected {shape}")
        rows = np.flatnonzero(np.any(mask > 0, axis=1))
        if rows.size and float(rows[0]) < head_y:
            return True
    return False


def _row_width(
    silhouette: np.ndarray, row: int, x_min: float, x_max: float
) -> float:
    height, width = silhouette.shape
    low_x = max(0, int(np.ceil(x_min)))
    high_x = min(width, int(np.floor(x_max)) + 1)
    if not 0 <= row < height or low_x >= high_x:
        raise ValueError("Requested body measurement lies outside the silhouette")
    occupied = np.flatnonzero(silhouette[row, low_x:high_x])
    if occupied.size == 0:
        raise ValueError(f"No silhouette pixels at row {row}")
    return float(occupied[-1] - occupied[0] + 1)


def _line_width(
    silhouette: np.ndarray,
    y: float,
    x_min: float,
    x_max: float,
) -> float:
    height = silhouette.shape[0]
    center = int(round(y))
    for offset in range(height):
        for row in (center - offset, center + offset) if offset else (center,):
            if 0 <= row < height:
                try:
                    return _row_width(silhouette, row, x_min, x_max)
                except ValueError:
                    continue
    raise ValueError(f"No silhouette pixels near measurement line y={y:.1f}")


def _circumference(width_cm: float, depth_ratio: float) -> float:
    if not isfinite(depth_ratio) or depth_ratio <= 0:
        raise ValueError("Depth ratios must be positive finite numbers")
    a = width_cm / 2
    b = width_cm * depth_ratio / 2
    return pi * (3 * (a + b) - sqrt((3 * a + b) * (a + 3 * b)))


def _distance(start: tuple[float, float], end: tuple[float, float]) -> float:
    return hypot(end[0] - start[0], end[1] - start[1])


def measure(
    keypoints: dict[str, Any], alpha: np.ndarray, height_cm: float, cfg: dict[str, Any]
) -> dict[str, float]:
    """Estimate body measurements in centimetres from pose points and a silhouette."""
    if not isfinite(height_cm) or height_cm <= 0:
        raise ValueError("height_cm must be a positive finite number")

    silhouette = _mask(alpha)
    occupied_rows = np.flatnonzero(np.any(silhouette, axis=1))
    if occupied_rows.size == 0:
        raise ValueError("alpha contains no foreground pixels")

    left_shoulder = _point(keypoints, "left_shoulder")
    right_shoulder = _point(keypoints, "right_shoulder")
    left_hip = _point(keypoints, "left_hip")
    right_hip = _point(keypoints, "right_hip")
    left_ankle = _point(keypoints, "left_ankle")
    right_ankle = _point(keypoints, "right_ankle")
    shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
    hip_y = (left_hip[1] + right_hip[1]) / 2
    if hip_y <= shoulder_y:
        raise ValueError("Hip keypoints must be below shoulder keypoints")

    foot_rows = [
        float(value[1])
        for name, value in keypoints.items()
        if (name.endswith("_ankle") or name.endswith("_heel"))
        and isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and len(value) >= 2
    ]
    if not foot_rows:
        raise ValueError("At least one ankle or heel keypoint is required")
    top_y = float(occupied_rows[0])
    pixel_height = max(float(occupied_rows[-1]), max(foot_rows)) - top_y

    face_rows = [
        _point(keypoints, name)[1]
        for name in ("nose", "left_eye", "right_eye", "left_ear", "right_ear")
        if name in keypoints
    ]
    if face_rows:
        head_y = min(face_rows)
        s04_cfg = cfg.get("stages", {}).get("s04_body_fit", {})
        hair_allowance = float(s04_cfg.get("hair_allowance_frac", 0.02))
        if not 0 <= hair_allowance < 1:
            raise ValueError("hair_allowance_frac must be in [0, 1)")
        if _mask_above_head(
            keypoints,
            ("hat", "hair", "hat_mask", "hair_mask"),
            head_y,
            silhouette.shape,
        ):
            pixel_height *= 1 - hair_allowance

    if pixel_height <= 0:
        raise ValueError("Computed pixel height must be positive")
    cm_per_px = height_cm / pixel_height

    shoulder_xs = (left_shoulder[0], right_shoulder[0])
    hip_xs = (left_hip[0], right_hip[0])
    torso_min = min(*shoulder_xs, *hip_xs)
    torso_max = max(*shoulder_xs, *hip_xs)
    torso_span = torso_max - torso_min
    if torso_span <= 0:
        raise ValueError("Shoulder and hip keypoints must span a positive width")
    x_min = torso_min - torso_span * 0.15
    x_max = torso_max + torso_span * 0.15

    bust_width = _line_width(
        silhouette, shoulder_y + (hip_y - shoulder_y) * 0.25, x_min, x_max
    )
    underbust_width = _line_width(
        silhouette, shoulder_y + (hip_y - shoulder_y) * 0.35, x_min, x_max
    )

    height_px = float(occupied_rows[-1] - occupied_rows[0])
    waist_start = int(round(shoulder_y + (hip_y - shoulder_y) * 0.40))
    waist_end = int(round(shoulder_y + (hip_y - shoulder_y) * 0.70))
    waist_width = min(
        _row_width(silhouette, row, x_min, x_max)
        for row in range(max(0, waist_start), min(silhouette.shape[0], waist_end + 1))
        if np.any(silhouette[row])
    )

    hip_start = max(0, int(np.floor(hip_y)))
    hip_end = min(silhouette.shape[0], int(np.ceil(hip_y + height_px * 0.15)) + 1)
    hips_width = max(
        _row_width(silhouette, row, x_min, x_max)
        for row in range(hip_start, hip_end)
        if np.any(silhouette[row])
    )

    depth_ratios = cfg.get("stages", {}).get("s04_body_fit", {}).get("depth_ratio", {})
    widths = {
        "bust": bust_width,
        "underbust": underbust_width,
        "waist": waist_width,
        "hips": hips_width,
    }
    measurements = {
        name: _circumference(width * cm_per_px, float(depth_ratios[name]))
        for name, width in widths.items()
    }
    measurements["height"] = float(height_cm)
    measurements["shoulder_width"] = (
        _distance(left_shoulder, right_shoulder) * 1.15 * cm_per_px
    )
    leg_lengths = (
        _distance(left_hip, left_ankle),
        _distance(right_hip, right_ankle),
    )
    measurements["inseam"] = sum(leg_lengths) / len(leg_lengths) * 0.92 * cm_per_px
    return measurements
