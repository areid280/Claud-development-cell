from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import jsonschema

from avatar_forge.core.paths import SCHEMA_DIR
from avatar_forge.core.stage import StageContext
from avatar_forge.stages import s05_body_params


def _body() -> dict[str, Any]:
    return {
        "units": "cm",
        "source": "s04_body_fit",
        "measurements": {
            "height": 168.0,
            "bust": 90.0,
            "underbust": 75.0,
            "waist": 70.0,
            "hips": 96.0,
            "shoulder_width": 40.0,
            "inseam": 80.0,
        },
        "confidence": {"height": 0.5, "bust": 0.5},
        "colors": {"hair": "#2b2420", "skin": "#c08060", "eyes": "#5a7a8c"},
        "body_type_hint": "feminine",
    }


def _context(
    tmp_path: Path, sets: dict[str, str] | None = None
) -> StageContext:
    input_dir = tmp_path / "s04_body_fit"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "body_fit.json").write_text(
        json.dumps(_body()), encoding="utf-8"
    )
    return StageContext(
        name="s05_body_params",
        job_dir=tmp_path,
        stage_dir=tmp_path / "s05_body_params",
        config={},
        manifest={},
        overrides={"set": sets or {}},
        logger=logging.getLogger(__name__),
    )


def test_run_without_overrides_writes_schema_valid_body(tmp_path: Path) -> None:
    ctx = _context(tmp_path)

    result = s05_body_params.run(ctx)

    output_path = ctx.stage_dir / "body_params.json"
    body = json.loads(output_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (SCHEMA_DIR / "body_params.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(body, schema)
    assert result.status == "ok"
    assert result.outputs == ["s05_body_params/body_params.json"]
    assert body["source"] == "s05_body_params"
    assert body["body_type_hint"] == "feminine"
    assert "normalise" not in body
    assert result.data == {"normalised": False, "changes": {}, "overrides": {}}


def test_run_reports_warnings_and_applied_overrides(tmp_path: Path) -> None:
    ctx = _context(
        tmp_path,
        {"bust": "+10%", "hair_color": "#2B1D14", "unknown": "value"},
    )

    result = s05_body_params.run(ctx)

    body = json.loads(
        (ctx.stage_dir / "body_params.json").read_text(encoding="utf-8")
    )
    assert result.status == "warn"
    assert result.messages == ["Unknown setting 'unknown' ignored."]
    assert body["measurements"]["bust"] == 99.0
    assert body["colors"]["hair"] == "#2b1d14"
    assert result.data["overrides"] == {
        "bust": {"from": 90.0, "to": 99.0},
        "hair": {"from": "#2b2420", "to": "#2b1d14"},
    }
