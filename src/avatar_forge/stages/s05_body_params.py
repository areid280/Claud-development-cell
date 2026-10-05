"""s05_body_params — apply user overrides, then normalise, to get final body parameters.

Implemented by task T24 (overrides) and T40 (normalise).

Reads:   s04_body_fit/body_fit.json, ctx.overrides (from manifest "overrides")
Writes:  s05_body_params/body_params.json   validates against schemas/body_params.schema.json
Data:    {"normalised": bool, "changes": {...}}  what normalise changed and why
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T24")
