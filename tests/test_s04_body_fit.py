from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image

from avatar_forge.core.stage import StageContext
from avatar_forge.stages import s04_body_fit


def test_body_fit_writes_schema_data_and_height_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare_dir = tmp_path / "s02_prepare"
    parse_dir = tmp_path / "s03_parse"
    stage_dir = tmp_path / "s04_body_fit"
    prepare_dir.mkdir()
    parse_dir.mkdir()
    (parse_dir / "front").mkdir()

    Image.new("RGBA", (2, 2), (100, 120, 140, 255)).save(
        prepare_dir / "front_rgba.png"
    )
    (prepare_dir / "front_keypoints.json").write_text(
        json.dumps([{"score": 0.9, "keypoints": {}}]), encoding="utf-8"
    )
    Image.fromarray(np.array([[255, 0], [0, 0]], dtype=np.uint8)).save(
        parse_dir / "front" / "skin_mask.png"
    )
    (parse_dir / "parts.json").write_text(
        json.dumps(
            [
                {
                    "view": "front",
                    "label": "skin",
                    "mask": "s03_parse/front/skin_mask.png",
                }
            ]
        ),
        encoding="utf-8",
    )

    def fake_measure(
        keypoints: dict[str, Any],
        alpha: np.ndarray,
        height_cm: float,
        cfg: dict[str, Any],
    ) -> dict[str, float]:
        return {
            "height": height_cm,
            "bust": 90.0,
            "underbust": 75.0,
            "waist": 70.0,
            "hips": 95.0,
            "shoulder_width": 40.0,
            "inseam": 80.0,
        }

    monkeypatch.setattr(s04_body_fit, "measure", fake_measure)
    ctx = StageContext(
        name="s04_body_fit",
        job_dir=tmp_path,
        stage_dir=stage_dir,
        config={
            "stages": {
                "s04_body_fit": {
                    "default_height_cm": 168,
                    "default_eye_color": "#5a7a8c",
                    "body_type_hint": "feminine",
                }
            }
        },
        manifest={"inputs": [{"view": "front"}]},
        overrides={"set": {"height": "175"}},  # CLI values are strings (manifest schema)
        logger=logging.getLogger(__name__),
    )

    result = s04_body_fit.run(ctx)

    assert result.status == "ok"
    assert result.data == {"height_source": "override", "height_cm": 175.0}
    body_fit = json.loads((stage_dir / "body_fit.json").read_text(encoding="utf-8"))
    assert "height_source" not in body_fit
    assert body_fit["measurements"]["height"] == 175.0
    assert body_fit["colors"] == {
        "skin": "#64788c",
        "hair": "#2b2420",
        "eyes": "#5a7a8c",
    }


def test_body_fit_fails_without_front_input(tmp_path: Path) -> None:
    ctx = StageContext(
        name="s04_body_fit",
        job_dir=tmp_path,
        stage_dir=tmp_path / "s04_body_fit",
        config={},
        manifest={"inputs": [{"view": "back"}]},
        overrides={},
        logger=logging.getLogger(__name__),
    )

    result = s04_body_fit.run(ctx)

    assert result.status == "fail"
    assert result.messages == ["s04_body_fit requires a front input"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("175", 175.0),
        (" 162.5 ", 162.5),
        (175, 175.0),
        (170.5, 170.5),
        ("+5", None),
        ("-3", None),
        ("+10%", None),
        ("0", None),
        ("tall", None),
        (True, None),
        (None, None),
    ],
)
def test_absolute_height_accepts_cli_strings_and_skips_relative_forms(
    value: object, expected: float | None
) -> None:
    assert s04_body_fit._absolute_height(value) == expected
