from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from avatar_forge.body.keypoint_ratio import measure
from avatar_forge.core.config import load_pipeline_config, load_yaml
from avatar_forge.core.paths import REPO_ROOT
from avatar_forge.models.pose_rtmlib_rtmw import RTMLibRTMW
from avatar_forge.models.trials import register

REFERENCE_PATH = REPO_ROOT / "samples" / "reference.yaml"


@register("body_measure", "keypoint-ratio")
def trial_keypoint_ratio(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    trial_root = out_dir.parents[2]
    cutout_path = (
        trial_root / "bg_remove" / "birefnet" / image_path.stem / "cutout.png"
    )
    keypoints_path = (
        trial_root / "pose" / "rtmlib-rtmw" / image_path.stem / "keypoints.json"
    )
    if not cutout_path.is_file():
        raise FileNotFoundError(
            f"BiRefNet cut-out required for keypoint-ratio trial: {cutout_path}"
        )

    with Image.open(image_path) as source_image:
        image = source_image.convert("RGB")
    with Image.open(cutout_path) as source_cutout:
        cutout = source_cutout.convert("RGBA")
    if cutout.size != image.size:
        raise ValueError(
            f"BiRefNet cut-out size {cutout.size} does not match input {image.size}"
        )

    references = load_yaml(REFERENCE_PATH) if REFERENCE_PATH.is_file() else {}
    reference = references.get(image_path.stem, {})
    cfg = load_pipeline_config()
    body_cfg = cfg["stages"]["s04_body_fit"]
    height_cm = float(reference.get("height", body_cfg["default_height_cm"]))

    if keypoints_path.is_file():
        with keypoints_path.open(encoding="utf-8") as keypoints_file:
            people = json.load(keypoints_file)
    else:
        with RTMLibRTMW(entry) as pose_model:
            people = pose_model.predict(image)
    if not people:
        raise ValueError(f"Pose model found no people in {image_path}")
    person = max(people, key=lambda candidate: candidate["score"])
    alpha = np.asarray(cutout.getchannel("A"))
    measurements = measure(person["keypoints"], alpha, height_cm, cfg)

    output = {
        "units": "cm",
        "source": "trial:keypoint-ratio",
        "measurements": measurements,
    }
    measurements_path = out_dir / "measurements.json"
    measurements_path.write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "measurements": str(measurements_path),
        "height_cm": height_cm,
        "measurement_values_cm": measurements,
    }
