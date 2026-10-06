"""s00_ingest — normalise input images and record their metadata.

Implemented by task T02.

Reads:   inputs/<view>.<ext>  (copied there by core.job.create_job)
Writes:  s00_ingest/<view>.png   EXIF-rotated, RGB(A), 8-bit PNG
Data:    {"views": {"front": {"width": int, "height": int, "sha256": str,
                              "downscaled": bool}, ...}}
"""

from __future__ import annotations

import hashlib

from PIL import Image, ImageOps

from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    outputs: list[str] = []
    views: dict[str, dict[str, int | str | bool]] = {}
    max_long_side = ctx.stage_config()["max_long_side_px"]

    for entry in ctx.manifest["inputs"]:
        view = entry["view"]
        input_path = ctx.job_dir / entry["path"]
        try:
            with Image.open(input_path) as source:
                image = ImageOps.exif_transpose(source)
                has_alpha = "A" in image.getbands() or "transparency" in image.info
                image = image.convert("RGBA" if has_alpha else "RGB")
                long_side = max(image.size)
                downscaled = long_side > max_long_side
                if downscaled:
                    scale = max_long_side / long_side
                    size = (round(image.width * scale), round(image.height * scale))
                    image = image.resize(size, Image.Resampling.LANCZOS)
        except (OSError, ValueError) as error:
            return StageResult(
                status="fail",
                messages=[f"Cannot read {view} image: {error}"],
            )

        with input_path.open("rb") as input_file:
            digest = hashlib.file_digest(input_file, "sha256").hexdigest()
        output_path = ctx.stage_dir / f"{view}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG")

        outputs.append(output_path.relative_to(ctx.job_dir).as_posix())
        views[view] = {
            "width": image.width,
            "height": image.height,
            "sha256": digest,
            "downscaled": downscaled,
        }

    return StageResult(status="ok", outputs=outputs, data={"views": views})
