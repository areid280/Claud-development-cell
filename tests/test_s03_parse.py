from __future__ import annotations

import numpy as np

from avatar_forge.stages.parse_post import postprocess_masks


def test_postprocess_masks_removes_transparency_and_small_parts() -> None:
    alpha = np.ones((8, 10), dtype=bool)
    alpha[:, 0] = False
    mask = np.zeros_like(alpha)
    mask[1:4, 1:4] = True
    mask[1:4, 6:9] = True
    mask[6, 4] = True
    mask[0, 0] = True
    small_mask = np.zeros_like(alpha)
    small_mask[5, 5:7] = True

    result = postprocess_masks(
        {"boots": mask, "speck": small_mask}, alpha, min_area=3
    )

    assert "speck" not in result
    processed, instances = result["boots"]
    assert not processed[0, 0]
    assert int(processed.sum()) == 19
    assert instances == 2
