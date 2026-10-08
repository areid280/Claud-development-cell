from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from avatar_forge.body.keypoint_ratio import measure
from avatar_forge.core.config import load_pipeline_config


@pytest.fixture
def keypoints() -> dict[str, Any]:
    return {
        "nose": [50, 20, 1],
        "left_eye": [46, 18, 1],
        "right_eye": [54, 18, 1],
        "left_shoulder": [25, 30, 1],
        "right_shoulder": [75, 30, 1],
        "left_hip": [30, 65, 1],
        "right_hip": [70, 65, 1],
        "left_knee": [38, 86, 1],
        "right_knee": [62, 86, 1],
        "left_ankle": [40, 108, 1],
        "right_ankle": [60, 108, 1],
    }


def _rectangle(width: int) -> np.ndarray:
    alpha = np.zeros((120, 100), dtype=np.uint8)
    left = (100 - width) // 2
    alpha[10:111, left : left + width] = 255
    return alpha


def test_measure_scales_from_alpha_and_foot_extent(
    keypoints: dict[str, Any],
) -> None:
    result = measure(keypoints, _rectangle(60), 200, load_pipeline_config())

    assert result["height"] == 200
    assert result["shoulder_width"] == pytest.approx(115)
    assert result["inseam"] == pytest.approx(np.hypot(10, 43) * 0.92 * 2)
    assert result["bust"] > 0
    assert result["underbust"] > 0
    assert result["waist"] > 0
    assert result["hips"] > 0


def test_wider_silhouette_increases_circumferences(
    keypoints: dict[str, Any],
) -> None:
    cfg = load_pipeline_config()
    narrow = measure(keypoints, _rectangle(52), 168, cfg)
    wide = measure(keypoints, _rectangle(68), 168, cfg)

    for measurement in ("bust", "underbust", "waist", "hips"):
        assert wide[measurement] > narrow[measurement]


def test_hair_mask_above_face_applies_height_allowance(
    keypoints: dict[str, Any],
) -> None:
    alpha = _rectangle(60)
    hair_mask = np.zeros_like(alpha)
    hair_mask[10:18, 48:53] = 255
    keypoints["hair"] = hair_mask

    corrected = measure(keypoints, alpha, 168, load_pipeline_config())
    without_mask = measure(
        {name: point for name, point in keypoints.items() if name != "hair"},
        alpha,
        168,
        load_pipeline_config(),
    )

    assert corrected["shoulder_width"] > without_mask["shoulder_width"]
