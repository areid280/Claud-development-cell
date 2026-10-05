"""s07_texture — project image colours onto each garment's UVs and build PBR maps.

Implemented by task T36 (single view) and T51 (multi-view fusion).

Reads:   s06_garments/<garment_id>/raw.glb, s02_prepare/<view>_rgba.png, s03_parse masks
Writes:  s07_texture/<garment_id>/{basecolor,normal,roughness,metallic}.png
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T36")
