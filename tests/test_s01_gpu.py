from __future__ import annotations

import json
from pathlib import Path

import pytest

from avatar_forge.core.config import load_pipeline_config
from avatar_forge.core.job import create_job
from avatar_forge.core.runner import StageFailedError, run_job


@pytest.mark.gpu
def test_bad_cropped_feet_sample_fails(jobs_dir: Path) -> None:
    sample = Path("samples/bad_cropped_feet.png")
    if not sample.exists():
        pytest.skip("sample missing")

    job = create_job(
        {"front": sample},
        adult_confirmed=True,
        consent_confirmed=True,
        root=jobs_dir,
    )
    with pytest.raises(StageFailedError, match="Feet"):
        run_job(job, load_pipeline_config(), to_stage="s01_validate")

    payload = json.loads((job / "s01_validate" / "report.json").read_text(encoding="utf-8"))
    assert payload["front"]["status"] == "fail"
    assert any("Feet" in message for message in payload["front"]["messages"])
