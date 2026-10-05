"""s08_assemble — Blender headless: body + garments, skinning, anti-clipping, LODs.

Implemented by task T37 (assemble) and T45 (LODs).

Reads:   s05_body_params, s06_garments, s07_texture, assets/body_base/, assets/garment_library/
Writes:  s08_assemble/character.blend, s08_assemble/previews/{front,back}.png
Runs:    blender --background --python src/avatar_forge/blender/assemble.py -- <args>
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T37")
