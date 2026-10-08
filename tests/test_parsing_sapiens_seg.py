from __future__ import annotations

import numpy as np
from PIL import Image

from avatar_forge.models.parsing_sapiens_seg import (
    GOLIATH_CLASSES,
    INPUT_MEAN,
    INPUT_STD,
    MODEL_LABEL_MAP,
    preprocess_sapiens_image,
)
from avatar_forge.models.parsing_utils import label_key


def test_preprocess_sapiens_image_resizes_and_normalizes() -> None:
    image = Image.new("RGB", (2, 3), (123, 116, 103))

    result = preprocess_sapiens_image(image)

    assert result.shape == (3, 1024, 768)
    expected = (np.array([123, 116, 103], dtype=np.float32) - INPUT_MEAN) / INPUT_STD
    np.testing.assert_allclose(result[:, 0, 0], expected)


def test_goliath_classes_are_mapped_to_canonical_labels() -> None:
    assert len(GOLIATH_CLASSES) == 28
    assert {
        label_key(label): canonical for label, canonical in MODEL_LABEL_MAP.items()
    } == {
        "background": "background",
        "apparel": "accessory",
        "face neck": "face",
        "hair": "hair",
        "left foot": "skin",
        "left hand": "skin",
        "left lower arm": "skin",
        "left lower leg": "skin",
        "left shoe": "shoes",
        "left sock": "socks_stockings",
        "left upper arm": "skin",
        "left upper leg": "skin",
        "lower clothing": "lower_clothes",
        "right foot": "skin",
        "right hand": "skin",
        "right lower arm": "skin",
        "right lower leg": "skin",
        "right shoe": "shoes",
        "right sock": "socks_stockings",
        "right upper arm": "skin",
        "right upper leg": "skin",
        "torso": "skin",
        "upper clothing": "upper_clothes",
        "lower lip": "face",
        "upper lip": "face",
        "lower teeth": "face",
        "upper teeth": "face",
        "tongue": "face",
    }
    assert {label_key(label) for label in GOLIATH_CLASSES} == set(MODEL_LABEL_MAP)
