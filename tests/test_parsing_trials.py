from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from avatar_forge.models.trial_adapters_parsing import write_parsing_outputs


def test_write_parsing_outputs_creates_masks_and_colour_labels(
    tmp_path: Path,
) -> None:
    hair_mask = np.zeros((3, 4), dtype=bool)
    hair_mask[0, 1:3] = True
    unknown_mask = np.zeros((3, 4), dtype=bool)
    unknown_mask[2, 0] = True

    write_parsing_outputs(
        {"hair": hair_mask, "unknown-model-label": unknown_mask},
        tmp_path,
        (4, 3),
    )

    saved_hair = np.asarray(Image.open(tmp_path / "masks" / "hair.png"))
    saved_accessory = np.asarray(Image.open(tmp_path / "masks" / "accessory.png"))
    labels = np.asarray(Image.open(tmp_path / "labels.png"))
    parts = json.loads((tmp_path / "parts.json").read_text(encoding="utf-8"))

    assert saved_hair[0, 1:3].tolist() == [255, 255]
    assert saved_accessory[2, 0] == 255
    assert labels[0, 1].tolist() == [80, 40, 20]
    assert labels[2, 0].tolist() == [250, 100, 30]
    assert parts["hair"] == 2
    assert parts["accessory"] == 1


def test_write_parsing_outputs_rejects_wrong_mask_shape(tmp_path: Path) -> None:
    mask = np.zeros((2, 2), dtype=bool)

    with pytest.raises(ValueError, match=r"expected \(3, 4\)"):
        write_parsing_outputs({"hair": mask}, tmp_path, (4, 3))
