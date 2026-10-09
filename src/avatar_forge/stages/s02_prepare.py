"""s02_prepare — remove backgrounds and crop each person consistently.

Reads:   s00_ingest/<view>.png, s01_validate/<view>_keypoints.json
Writes:  s02_prepare/<view>_rgba.png, <view>_crop.json, <view>_keypoints.json
"""

from __future__ import annotations

import json
from typing import Any

from PIL import Image

from avatar_forge.core.stage import StageContext, StageResult
from avatar_forge.models.registry import load_selected
from avatar_forge.stages.crop_math import crop_box


def _transform_person(
    person: dict[str, Any], box: tuple[int, int, int, int], scale: float
) -> dict[str, Any]:
    x0, y0, _, _ = box
    transformed = dict(person)
    transformed["bbox"] = [
        (float(value) - offset) * scale
        for value, offset in zip(person["bbox"], (x0, y0, x0, y0), strict=True)
    ]
    transformed["keypoints"] = {
        name: [(float(point[0]) - x0) * scale, (float(point[1]) - y0) * scale, *point[2:]]
        for name, point in person["keypoints"].items()
    }
    return transformed


def run(ctx: StageContext) -> StageResult:
    cfg = ctx.stage_config()
    output_long_side = int(cfg["output_long_side_px"])
    margin_frac = float(cfg["crop_margin_frac"])
    keypoint_min_score = float(
        ctx.config["stages"]["s01_validate"]["keypoint_min_score"]
    )
    ctx.stage_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[str] = []
    views: dict[str, dict[str, Any]] = {}
    with load_selected("bg_remove") as model:
        for item in ctx.manifest.get("inputs", []):
            view = str(item["view"])
            source_path = ctx.job_dir / "s00_ingest" / f"{view}.png"
            keypoints_path = ctx.job_dir / "s01_validate" / f"{view}_keypoints.json"
            with Image.open(source_path) as image:
                rgba = model.predict(image)

            alpha_bbox = rgba.getchannel("A").getbbox()
            if alpha_bbox is None:
                return StageResult(
                    status="fail",
                    outputs=outputs,
                    messages=[f"{view}: nothing left after background removal"],
                    data={"views": views},
                )

            persons: list[dict[str, Any]] = json.loads(
                keypoints_path.read_text(encoding="utf-8")
            )
            confident_persons = [
                person
                for person in persons
                if float(person["score"]) >= keypoint_min_score
            ]
            best_person = max(
                confident_persons, key=lambda person: float(person["score"]), default=None
            )
            kp_bbox = tuple(best_person["bbox"]) if best_person is not None else None
            box = crop_box(alpha_bbox, kp_bbox, rgba.size, margin_frac)
            x0, y0, x1, y1 = box
            cropped = rgba.crop(box)
            scale = output_long_side / max(cropped.size)
            output_size = (
                round(cropped.width * scale),
                round(cropped.height * scale),
            )
            prepared = cropped.resize(output_size, Image.Resampling.LANCZOS)

            rgba_output = ctx.stage_dir / f"{view}_rgba.png"
            prepared.save(rgba_output)
            crop_output = ctx.stage_dir / f"{view}_crop.json"
            crop_output.write_text(
                json.dumps(
                    {
                        "box": [x0, y0, x1, y1],
                        "scale": scale,
                        "size": list(output_size),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            transformed_keypoints_path = ctx.stage_dir / f"{view}_keypoints.json"
            transformed_keypoints_path.write_text(
                json.dumps(
                    [_transform_person(person, box, scale) for person in persons],
                    indent=2,
                ),
                encoding="utf-8",
            )

            outputs.extend(
                path.relative_to(ctx.job_dir).as_posix()
                for path in (rgba_output, crop_output, transformed_keypoints_path)
            )
            views[view] = {"box": [x0, y0, x1, y1], "scale": scale}

    return StageResult(status="ok", outputs=outputs, data={"views": views})
