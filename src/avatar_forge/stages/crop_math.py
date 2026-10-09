"""Crop-box calculations shared by the preparation stage."""

from __future__ import annotations

import math


def crop_box(
    alpha_bbox: tuple[int, int, int, int],
    kp_bbox: tuple[int, int, int, int] | None,
    image_size: tuple[int, int],
    margin_frac: float,
) -> tuple[int, int, int, int]:
    """Return the clamped union of alpha/keypoint boxes with height-based margin."""
    boxes = (alpha_bbox,) if kp_bbox is None else (alpha_bbox, kp_bbox)
    left = min(box[0] for box in boxes)
    top = min(box[1] for box in boxes)
    right = max(box[2] for box in boxes)
    bottom = max(box[3] for box in boxes)
    margin = (bottom - top) * margin_frac
    width, height = image_size
    return (
        max(0, math.floor(left - margin)),
        max(0, math.floor(top - margin)),
        min(width, math.ceil(right + margin)),
        min(height, math.ceil(bottom + margin)),
    )
