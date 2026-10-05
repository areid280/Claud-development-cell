"""s02_prepare — background removal, crop to the person, colour normalise.

Implemented by task T21.

Reads:   s00_ingest/<view>.png, s01_validate/<view>_keypoints.json
Writes:  s02_prepare/<view>_rgba.png   person on transparent background, cropped with margin
         s02_prepare/<view>_crop.json  crop box in original pixel coords
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T21")
