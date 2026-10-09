from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from avatar_forge.models.i23d_triposr import prepare_model_input
from avatar_forge.models.trial_adapters_i23d import _garment_crop


def test_prepare_model_input_crops_foreground_and_composites_grey() -> None:
    image = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    for x in range(2, 6):
        for y in range(2, 8):
            image.putpixel((x, y), (200, 40, 20, 255))

    prepared = prepare_model_input(image)

    assert prepared.shape == (7, 7, 3)
    assert tuple(prepared[0, 0]) == (127, 127, 127)
    assert tuple(prepared[3, 3]) == (200, 40, 20)


def test_garment_crop_uses_valid_mask_and_makes_other_pixels_transparent(
    tmp_path: Path,
) -> None:
    trial_dir = tmp_path / "parsing" / "florence2-plus-sam" / "sample"
    mask_dir = trial_dir / "masks"
    mask_dir.mkdir(parents=True)
    (trial_dir / "trial.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    mask = np.zeros((8, 8), dtype=np.uint8)
    mask[2:6, 2:6] = 255
    Image.fromarray(mask).save(mask_dir / "boots.png")
    cutout = Image.new("RGBA", (8, 8), (220, 30, 10, 255))

    cropped, source = _garment_crop(cutout, tmp_path, "sample")

    assert source == "florence2-plus-sam/boots"
    assert cropped.size == (6, 6)
    alpha = np.asarray(cropped.getchannel("A"))
    assert np.count_nonzero(alpha) == 16
    assert alpha[1, 1] == 255
    assert alpha[0, 0] == 0
