from __future__ import annotations

import json
from pathlib import Path

from scripts.trials_report import build_report


def test_report_shows_percentage_error_for_body_measurements(
    tmp_path: Path,
) -> None:
    out_root = tmp_path / "trials"
    trial_dir = out_root / "body_measure" / "keypoint-ratio" / "a_front"
    trial_dir.mkdir(parents=True)
    (out_root / "body_measure" / "keypoint-ratio" / "summary.json").write_text(
        json.dumps(
            {
                "role": "body_measure",
                "name": "keypoint-ratio",
                "ok": 1,
                "total": 1,
                "mean_seconds": 1.0,
                "max_vram_gb": 0.0,
            }
        ),
        encoding="utf-8",
    )
    (trial_dir / "trial.json").write_text(
        json.dumps(
            {
                "role": "body_measure",
                "name": "keypoint-ratio",
                "image": "samples/a_front.png",
            }
        ),
        encoding="utf-8",
    )
    (trial_dir / "measurements.json").write_text(
        json.dumps({"measurements": {"height": 168, "bust": 81}}),
        encoding="utf-8",
    )
    references = tmp_path / "reference.yaml"
    references.write_text(
        "a_front: {height: 168, bust: 90}\n", encoding="utf-8"
    )

    report = build_report(out_root, references)

    assert "## body_measure" in report
    assert "Measurement errors vs owner references:" in report
    assert "| `a_front` | height | 168.00 | 168.00 | 0.00% |" in report
    assert "| `a_front` | bust | 90.00 | 81.00 | 10.00% |" in report


def test_report_omits_measurement_errors_without_reference_file(
    tmp_path: Path,
) -> None:
    report = build_report(tmp_path, tmp_path / "missing-reference.yaml")

    assert "Measurement errors vs owner references:" not in report
