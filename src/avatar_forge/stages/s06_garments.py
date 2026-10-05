"""s06_garments — one mesh per garment.

MVP (task T25): mode "mvp_fused" builds a single fused mesh of the whole figure.
M3 (tasks T30–T35): mode "separate" classifies each garment and uses its strategy
(skin_layer / template / generated).

Reads:   s02_prepare, s03_parse, s05_body_params
Writes:  s06_garments/fused/character_fused.glb              (mvp_fused)
         s06_garments/<garment_id>/raw.glb + garment.json   (separate; garment.schema.json)
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T25")
