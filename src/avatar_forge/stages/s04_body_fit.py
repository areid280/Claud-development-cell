"""s04_body_fit — estimate body measurements (cm) and skin/hair/eye colours.

Implemented by task T23.

Reads:   s02_prepare/<view>_rgba.png, s03_parse/parts.json
Writes:  s04_body_fit/body_fit.json   must validate against schemas/body_params.schema.json
Note:    Output measurements, not body-model parameters (docs/05_DECISIONS.md D-001).
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T23")
