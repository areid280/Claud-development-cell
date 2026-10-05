"""s00_ingest — normalise input images and record their metadata.

Implemented by task T02.

Reads:   inputs/<view>.<ext>  (copied there by core.job.create_job)
Writes:  s00_ingest/<view>.png   EXIF-rotated, RGB(A), 8-bit PNG
Data:    {"views": {"front": {"width": int, "height": int, "sha256": str}, ...}}
"""

from __future__ import annotations

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    return StageResult.not_implemented("T02")
