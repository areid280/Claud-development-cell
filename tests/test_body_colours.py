from __future__ import annotations

import numpy as np
import pytest

from avatar_forge.body.colours import median_color_hex


def test_median_color_hex_trims_darkest_and_brightest_ten_percent() -> None:
    shades = np.arange(11, dtype=np.uint8)
    rgb = np.repeat(shades[:, None, None], 3, axis=2)
    mask = np.ones(rgb.shape[:2], dtype=bool)

    assert median_color_hex(rgb, mask) == "#050505"


def test_median_color_hex_uses_only_masked_pixels() -> None:
    rgb = np.array([[[255, 255, 255], [10, 20, 30]]], dtype=np.uint8)
    mask = np.array([[False, True]])

    assert median_color_hex(rgb, mask) == "#0a141e"


def test_median_color_hex_rejects_empty_mask() -> None:
    with pytest.raises(ValueError, match="mask contains no pixels"):
        median_color_hex(np.zeros((2, 2, 3)), np.zeros((2, 2), dtype=bool))


def test_median_color_hex_rejects_mismatched_mask_shape() -> None:
    with pytest.raises(ValueError, match="expected"):
        median_color_hex(np.zeros((2, 2, 3)), np.ones((2, 1), dtype=bool))
