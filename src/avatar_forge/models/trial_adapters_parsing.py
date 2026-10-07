from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from avatar_forge.core.config import load_pipeline_config
from avatar_forge.models.parsing_florence2_plus_sam2 import Florence2PlusSam2
from avatar_forge.models.parsing_sapiens_seg import SapiensSeg
from avatar_forge.models.parsing_segformer_clothes import SegformerClothes
from avatar_forge.models.trials import register

LABEL_COLORS = {
    "background": (0, 0, 0),
    "hair": (80, 40, 20),
    "face": (255, 200, 170),
    "skin": (240, 160, 120),
    "neck": (220, 140, 110),
    "upper_clothes": (40, 110, 220),
    "lower_clothes": (30, 70, 180),
    "dress": (200, 40, 150),
    "bodysuit": (160, 30, 120),
    "jacket": (30, 160, 220),
    "gloves": (240, 220, 30),
    "belt": (130, 80, 40),
    "collar": (80, 220, 220),
    "hat": (180, 120, 40),
    "shoes": (80, 80, 80),
    "boots": (50, 50, 50),
    "socks_stockings": (220, 100, 170),
    "bag": (100, 180, 70),
    "accessory": (250, 100, 30),
}


def write_parsing_outputs(
    masks: dict[str, np.ndarray], out_dir: Path, image_size: tuple[int, int]
) -> dict[str, Any]:
    width, height = image_size
    labels = list(load_pipeline_config()["stages"]["s03_parse"]["labels"])
    if "accessory" not in labels:
        raise ValueError("Canonical parsing labels must contain 'accessory'")

    normalized: dict[str, np.ndarray] = {}
    for label, raw_mask in masks.items():
        if label not in labels:
            label = "accessory"
        mask = np.asarray(raw_mask, dtype=bool)
        if mask.shape != (height, width):
            raise ValueError(
                f"Mask {label!r} has shape {mask.shape}; expected {(height, width)}"
            )
        normalized[label] = normalized.get(
            label, np.zeros((height, width), dtype=bool)
        ) | mask

    masks_dir = out_dir / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)
    parts: dict[str, int] = {}
    label_image = np.zeros((height, width, 3), dtype=np.uint8)
    label_image[:] = LABEL_COLORS["background"]

    for label in labels:
        mask = normalized.get(label, np.zeros((height, width), dtype=bool))
        Image.fromarray(mask.astype(np.uint8) * 255).save(masks_dir / f"{label}.png")
        parts[label] = int(mask.sum())
        if label != "background":
            label_image[mask] = LABEL_COLORS[label]

    Image.fromarray(label_image, mode="RGB").save(out_dir / "labels.png")
    (out_dir / "parts.json").write_text(
        json.dumps(parts, indent=2) + "\n", encoding="utf-8"
    )
    return {"labels": str(out_dir / "labels.png"), "parts": str(out_dir / "parts.json")}


def _parsing_trial(
    wrapper_type: type[Any],
    entry: dict[str, Any],
    image_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    image = Image.open(image_path).convert("RGBA")
    with wrapper_type(entry) as model:
        masks = model.predict(image)
    return write_parsing_outputs(masks, out_dir, image.size)


@register("parsing", "segformer-clothes")
def trial_segformer_clothes(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    return _parsing_trial(SegformerClothes, entry, image_path, out_dir)


@register("parsing", "florence2-plus-sam2")
def trial_florence2_plus_sam2(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    return _parsing_trial(Florence2PlusSam2, entry, image_path, out_dir)


@register("parsing", "sapiens-seg")
def trial_sapiens_seg(
    entry: dict[str, Any], image_path: Path, out_dir: Path
) -> dict[str, Any]:
    return _parsing_trial(SapiensSeg, entry, image_path, out_dir)
