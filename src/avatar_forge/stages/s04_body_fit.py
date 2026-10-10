"""s04_body_fit — estimate body measurements (cm) and skin/hair/eye colours.

Implemented by task T23.

Reads:   s02_prepare/<view>_rgba.png, s03_parse/parts.json
Writes:  s04_body_fit/body_fit.json   must validate against schemas/body_params.schema.json
Note:    Output measurements, not body-model parameters (docs/05_DECISIONS.md D-001).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import numpy as np
from PIL import Image

from avatar_forge.body.colours import median_color_hex
from avatar_forge.body.keypoint_ratio import measure
from avatar_forge.core.paths import SCHEMA_DIR
from avatar_forge.core.stage import StageContext, StageResult

_ABSOLUTE_NUMBER = re.compile(r"\d+(\.\d+)?")


def _color_mask(
    job_dir: Path,
    parts: list[dict[str, Any]],
    labels: set[str],
    shape: tuple[int, int],
) -> np.ndarray:
    combined = np.zeros(shape, dtype=bool)
    for part in parts:
        if part.get("label") not in labels:
            continue
        with Image.open(job_dir / part["mask"]) as opened_mask:
            mask = np.asarray(opened_mask) > 127
        if mask.shape != shape:
            raise ValueError(
                f"{part['label']} mask has shape {mask.shape}; expected {shape}"
            )
        combined |= mask
    return combined


def _absolute_height(value: Any) -> float | None:
    """An absolute height override in cm, or None.

    CLI ``--set`` values arrive as strings (``"175"``), so plain unsigned numbers are accepted in
    either form. Relative forms (``"+5"``, ``"-3%"``) return None: s05_body_params applies them.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str) and _ABSOLUTE_NUMBER.fullmatch(value.strip()):
        number = float(value.strip())
    else:
        return None
    return number if number > 0 else None


def run(ctx: StageContext) -> StageResult:
    inputs = ctx.manifest.get("inputs", [])
    front_input = next(
        (item for item in inputs if item.get("view") == "front"), None
    )
    if front_input is None:
        return StageResult(
            status="fail",
            messages=["s04_body_fit requires a front input"],
        )

    cfg = ctx.stage_config()
    override_height = _absolute_height(ctx.overrides.get("set", {}).get("height"))
    if override_height is not None:
        height_cm = override_height
        height_source = "override"
    else:
        height_cm = float(cfg["default_height_cm"])
        height_source = "default"

    rgba_path = ctx.previous_output("s02_prepare", "front_rgba.png")
    keypoints_path = ctx.previous_output("s02_prepare", "front_keypoints.json")
    parts_path = ctx.previous_output("s03_parse", "parts.json")
    with Image.open(rgba_path) as opened_rgba:
        rgba = opened_rgba.convert("RGBA")
        alpha = np.asarray(rgba.getchannel("A")).copy() > 0
        rgb = np.asarray(rgba.convert("RGB")).copy()

    people: list[dict[str, Any]] = json.loads(
        keypoints_path.read_text(encoding="utf-8")
    )
    if not people:
        return StageResult(
            status="fail",
            messages=["front_keypoints.json contains no people"],
        )
    person = max(people, key=lambda item: float(item["score"]))
    measurements = measure(person["keypoints"], alpha, height_cm, ctx.stage_config())

    parts: list[dict[str, Any]] = json.loads(
        parts_path.read_text(encoding="utf-8")
    )
    front_parts = [part for part in parts if part.get("view") == "front"]
    skin_mask = _color_mask(
        ctx.job_dir, front_parts, {"skin", "face"}, alpha.shape
    )
    hair_parts = [part for part in front_parts if part.get("label") == "hair"]
    hair_mask = (
        _color_mask(ctx.job_dir, hair_parts, {"hair"}, alpha.shape)
        if hair_parts
        else np.zeros(alpha.shape, dtype=bool)
    )
    colors = {
        "skin": median_color_hex(rgb, skin_mask),
        "hair": median_color_hex(rgb, hair_mask) if np.any(hair_mask) else "#2b2420",
        "eyes": str(cfg["default_eye_color"]),
    }

    data = {
        "units": "cm",
        "source": "s04_body_fit",
        "measurements": measurements,
        "confidence": {key: 0.5 for key in measurements},
        "colors": colors,
        "body_type_hint": cfg["body_type_hint"],
    }
    schema = json.loads(
        (SCHEMA_DIR / "body_params.schema.json").read_text(encoding="utf-8")
    )
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        return StageResult(
            status="fail",
            messages=[f"body_fit.json failed schema validation: {exc.message}"],
        )

    ctx.stage_dir.mkdir(parents=True, exist_ok=True)
    output_path = ctx.stage_dir / "body_fit.json"
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return StageResult(
        status="ok",
        outputs=[output_path.relative_to(ctx.job_dir).as_posix()],
        data={"height_source": height_source, "height_cm": height_cm},
    )
