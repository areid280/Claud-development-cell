from __future__ import annotations

import numpy as np
from scipy import ndimage


def postprocess_masks(
    masks: dict[str, np.ndarray], alpha: np.ndarray, min_area: int
) -> dict[str, tuple[np.ndarray, int]]:
    alpha_mask = np.asarray(alpha, dtype=bool)
    processed: dict[str, tuple[np.ndarray, int]] = {}
    connectivity = np.ones((3, 3), dtype=np.uint8)

    for label, source_mask in masks.items():
        source = np.asarray(source_mask, dtype=bool)
        if source.shape != alpha_mask.shape:
            raise ValueError(
                f"mask for {label!r} has shape {source.shape}; "
                f"expected {alpha_mask.shape}"
            )
        mask = source & alpha_mask
        area = int(mask.sum())
        if area < min_area:
            continue

        component_labels, component_count = ndimage.label(
            mask, structure=connectivity
        )
        if component_count == 0:
            continue
        component_sizes = np.bincount(component_labels.ravel())
        largest_size = int(component_sizes[1:].max())
        min_component_size = largest_size * 0.25
        instances = sum(
            int(component_sizes[component] >= min_component_size)
            for component in range(1, component_count + 1)
        )
        processed[label] = (mask, instances)

    return processed
