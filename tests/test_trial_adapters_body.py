from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from avatar_forge.models import trial_adapters_body


def _keypoints() -> dict[str, list[float]]:
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


def test_keypoint_ratio_trial_writes_measurements(
    tmp_path: Path, monkeypatch: Any
) -> None:
    image_path = tmp_path / "a_front.png"
    Image.new("RGB", (100, 120), (80, 80, 80)).save(image_path)

    trial_root = tmp_path / "trials"
    out_dir = trial_root / "body_measure" / "keypoint-ratio" / image_path.stem
    out_dir.mkdir(parents=True)
    cutout_path = (
        trial_root
        / "bg_remove"
        / "birefnet"
        / image_path.stem
        / "cutout.png"
    )
    cutout_path.parent.mkdir(parents=True)
    cutout = np.zeros((120, 100, 4), dtype=np.uint8)
    cutout[10:111, 20:80, :3] = 255
    cutout[10:111, 20:80, 3] = 255
    Image.fromarray(cutout).save(cutout_path)

    reference_path = tmp_path / "reference.yaml"
    reference_path.write_text("a_front: {height: 165}\n", encoding="utf-8")
    monkeypatch.setattr(trial_adapters_body, "REFERENCE_PATH", reference_path)

    class FakePose:
        def __init__(self, entry: dict[str, Any]) -> None:
            assert entry == {"name": "keypoint-ratio"}

        def __enter__(self) -> FakePose:
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def predict(self, image: Image.Image) -> list[dict[str, Any]]:
            assert image.size == (100, 120)
            return [{"score": 0.9, "keypoints": _keypoints()}]

    monkeypatch.setattr(trial_adapters_body, "RTMLibRTMW", FakePose)

    result = trial_adapters_body.trial_keypoint_ratio(
        {"name": "keypoint-ratio"}, image_path, out_dir
    )

    output_path = out_dir / "measurements.json"
    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["height_cm"] == 165
    assert output["units"] == "cm"
    assert output["measurements"]["height"] == 165
    assert {
        "bust",
        "underbust",
        "waist",
        "hips",
        "shoulder_width",
        "inseam",
    }.issubset(output["measurements"])
