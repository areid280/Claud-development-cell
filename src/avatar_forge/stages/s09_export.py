"""s09_export — FBX + textures + import_manifest.json for UE5.

Implemented by task T26 (MVP fused export) and T38 (per-garment export).

Reads:   s06_garments (MVP) or s08_assemble/character.blend, s07_texture, s05_body_params
Writes:  s09_export/<job_id>/  layout in docs/03_UE5_INTEGRATION.md §1
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T26")
