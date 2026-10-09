from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from avatar_forge.core.config import load_pipeline_config
from avatar_forge.core.job import create_job
from avatar_forge.core.runner import run_job
from avatar_forge.stages.crop_math import crop_box


def test_crop_box_clamps_to_image_edges() -> None:
    assert crop_box((2, 5, 18, 90), None, (20, 100), 0.1) == (0, 0, 20, 99)


def test_crop_box_unions_alpha_and_keypoint_boxes() -> None:
    assert crop_box((20, 20, 60, 80), (10, 5, 75, 90), (100, 100), 0.1) == (
        1,
        0,
        84,
        99,
    )


@pytest.mark.gpu
def test_prepare_sample_has_cutout_and_configured_long_side(tmp_path: Path) -> None:
    sample = Path("samples/a_front.png")
    if not sample.exists():
        pytest.skip("sample missing")

    job = create_job(
        {"front": sample},
        adult_confirmed=True,
        consent_confirmed=True,
        root=tmp_path,
    )
    run_job(job, load_pipeline_config(), to_stage="s02_prepare")

    with Image.open(job / "s02_prepare" / "front_rgba.png") as prepared:
        alpha_histogram = prepared.getchannel("A").histogram()
        assert sum(alpha_histogram[128:]) > prepared.width * prepared.height * 0.1
        assert max(prepared.size) == 2048

    crop = json.loads(
        (job / "s02_prepare" / "front_crop.json").read_text(encoding="utf-8")
    )
    assert crop["size"] == list(prepared.size)
