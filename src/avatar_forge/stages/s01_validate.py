"""s01_validate — check inputs meet the rules in docs/00_PROJECT_BRIEF.md §4.

Implemented by task T20.

Reads:   s00_ingest/<view>.png
Writes:  s01_validate/report.json, s01_validate/<view>_keypoints.json
Status:  "fail" if any hard rule fails (with a clear human reason),
         "warn" for soft issues (e.g. crossed arms), else "ok".
Config:  config/pipeline.yaml -> stages.s01_validate
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T20")
