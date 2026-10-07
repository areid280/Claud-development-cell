from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from avatar_forge.models.bg_remove_birefnet import BiRefNet
from avatar_forge.models.bg_remove_rembg import Rembg
from avatar_forge.models.pose_rtmlib_rtmw import RTMLibRTMW
from avatar_forge.models.pose_vitpose_hf import ViTPoseHF
from avatar_forge.models.trials import register

COCO_EDGES = (
    ("nose", "left_eye"),
    ("nose", "right_eye"),
    ("left_eye", "left_ear"),
    ("right_eye", "right_ear"),
    ("nose", "left_shoulder"),
    ("nose", "right_shoulder"),
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
)


def _pose_trial(
    wrapper_type: type[Any], entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(image_path).convert("RGB")
    with wrapper_type(entry) as model:
        people = model.predict(image)

    (out_dir / "keypoints.json").write_text(
        json.dumps(people, indent=2), encoding="utf-8"
    )
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    for person in people:
        points = person["keypoints"]
        for start, end in COCO_EDGES:
            if start in points and end in points:
                draw.line(
                    (tuple(points[start][:2]), tuple(points[end][:2])),
                    fill=(0, 255, 0),
                    width=3,
                )
        for point in points.values():
            x, y = point[:2]
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 64, 64))
    overlay.save(out_dir / "overlay.png")
    return {"people": len(people), "keypoints": str(out_dir / "keypoints.json")}


@register("pose", "rtmlib-rtmw")
def trial_rtmlib(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    return _pose_trial(RTMLibRTMW, entry, image_path, out_dir)


@register("pose", "vitpose-hf")
def trial_vitpose(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    return _pose_trial(ViTPoseHF, entry, image_path, out_dir)


def _background_trial(
    wrapper_type: type[Any], entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(image_path).convert("RGB")
    with wrapper_type(entry) as model:
        cutout = model.predict(image)

    cutout.save(out_dir / "cutout.png")
    background = Image.new("RGBA", cutout.size, (128, 128, 128, 255))
    background.alpha_composite(cutout)
    background.convert("RGB").save(out_dir / "on_grey.png")
    return {"cutout": str(out_dir / "cutout.png")}


@register("bg_remove", "birefnet")
def trial_birefnet(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    return _background_trial(BiRefNet, entry, image_path, out_dir)


@register("bg_remove", "rembg")
def trial_rembg(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    return _background_trial(Rembg, entry, image_path, out_dir)
