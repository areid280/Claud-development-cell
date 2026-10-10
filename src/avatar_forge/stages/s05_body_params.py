"""s05_body_params — apply user overrides to get final body parameters.

Normalisation is added later in T40.

Reads:   s04_body_fit/body_fit.json, ctx.overrides (from manifest "overrides")
Writes:  s05_body_params/body_params.json   validates against schemas/body_params.schema.json
Data:    {"normalised": bool, "changes": {...}, "overrides": {key: {"from", "to"}}}
"""

from __future__ import annotations

import json
from typing import Any

import jsonschema

from avatar_forge.body.overrides import COLOR_KEYS, MEASUREMENT_KEYS, apply_overrides
from avatar_forge.core.paths import SCHEMA_DIR
from avatar_forge.core.stage import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    body: dict[str, Any] = json.loads(
        ctx.previous_output("s04_body_fit", "body_fit.json").read_text(
            encoding="utf-8"
        )
    )
    new_body, messages = apply_overrides(body, ctx.overrides.get("set", {}))
    new_body["source"] = "s05_body_params"

    schema = json.loads(
        (SCHEMA_DIR / "body_params.schema.json").read_text(encoding="utf-8")
    )
    try:
        jsonschema.validate(new_body, schema)
    except jsonschema.ValidationError as exc:
        return StageResult(
            status="fail",
            messages=[f"body_params.json failed schema validation: {exc.message}"],
        )

    applied: dict[str, dict[str, Any]] = {}
    old_measurements = body["measurements"]
    new_measurements = new_body["measurements"]
    for key in MEASUREMENT_KEYS:
        old_value = old_measurements.get(key)
        if new_measurements.get(key) != old_value:
            applied[key] = {
                "from": old_value,
                "to": new_measurements[key],
            }
    old_colors = body["colors"]
    new_colors = new_body["colors"]
    for color_name in COLOR_KEYS.values():
        if new_colors[color_name] != old_colors[color_name]:
            applied[color_name] = {
                "from": old_colors[color_name],
                "to": new_colors[color_name],
            }

    ctx.stage_dir.mkdir(parents=True, exist_ok=True)
    output_path = ctx.stage_dir / "body_params.json"
    output_path.write_text(
        json.dumps(new_body, indent=2) + "\n", encoding="utf-8"
    )
    return StageResult(
        status="warn" if messages else "ok",
        outputs=[output_path.relative_to(ctx.job_dir).as_posix()],
        messages=messages,
        data={"normalised": False, "changes": {}, "overrides": applied},
    )
