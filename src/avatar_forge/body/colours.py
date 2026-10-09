from __future__ import annotations

import numpy as np


def median_color_hex(rgb: np.ndarray, mask: np.ndarray) -> str:
    """Return the trimmed median RGB color of masked pixels as a hex string."""
    pixels = np.asarray(rgb)
    selected = np.asarray(mask, dtype=bool)
    if pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError("rgb must have shape (height, width, 3)")
    if selected.shape != pixels.shape[:2]:
        raise ValueError(
            f"mask has shape {selected.shape}; expected {pixels.shape[:2]}"
        )
    values = pixels[selected].astype(np.float64)
    if values.size == 0:
        raise ValueError("mask contains no pixels")
    if not np.all(np.isfinite(values)) or np.any((values < 0) | (values > 255)):
        raise ValueError("rgb pixels must be finite values in [0, 255]")

    luminance = values @ np.array([0.2126, 0.7152, 0.0722])
    order = np.argsort(luminance)
    trim = int(len(values) * 0.1)
    if trim:
        order = order[trim:-trim]
    median = np.rint(np.median(values[order], axis=0)).astype(np.uint8)
    return f"#{median[0]:02x}{median[1]:02x}{median[2]:02x}"
