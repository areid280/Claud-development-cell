"""s03_parse — split each view into labelled part masks.

Implemented by task T22.

Reads:   s02_prepare/<view>_rgba.png
Writes:  s03_parse/<view>/<part>_mask.png   one binary mask per part
         s03_parse/parts.json               list of parts with label, view, area, bbox
Labels:  see config/pipeline.yaml -> stages.s03_parse.labels
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T22")
