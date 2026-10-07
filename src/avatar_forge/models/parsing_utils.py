from __future__ import annotations

import re
from collections.abc import Mapping

import numpy as np
from PIL import Image


def label_key(label: str) -> str:
    return re.sub(r"[_-]+", " ", label.strip().lower())


def image_rgb_and_alpha(image: Image.Image) -> tuple[Image.Image, np.ndarray]:
    rgba = image.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A")) > 0
    rgb = Image.new("RGB", rgba.size, (255, 255, 255))
    rgb.paste(rgba.convert("RGB"), mask=rgba.getchannel("A"))
    return rgb, alpha


def semantic_logits_to_masks(
    logits: object,
    id_to_label: Mapping[int | str, str],
    label_map: Mapping[str, str],
    image_size: tuple[int, int],
    alpha: np.ndarray,
) -> dict[str, np.ndarray]:
    import torch

    height, width = image_size
    if not isinstance(logits, torch.Tensor):
        raise TypeError("Segmentation logits must be a torch.Tensor")
    resized = torch.nn.functional.interpolate(
        logits,
        size=(height, width),
        mode="bilinear",
        align_corners=False,
    )
    class_ids = resized.argmax(dim=1)[0].detach().cpu().numpy()
    masks: dict[str, np.ndarray] = {}

    for raw_class_id, label in id_to_label.items():
        canonical = label_map.get(label_key(label), "accessory")
        class_mask = (class_ids == int(raw_class_id)) & alpha
        if not class_mask.any():
            continue
        if canonical not in masks:
            masks[canonical] = np.zeros((height, width), dtype=bool)
        masks[canonical] |= class_mask

    return masks


def id_to_label_map(id_to_label: Mapping[object, str]) -> dict[int, str]:
    return {int(class_id): str(label) for class_id, label in id_to_label.items()}
