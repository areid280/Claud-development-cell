from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from PIL import Image

from avatar_forge.core.config import load_pipeline_config
from avatar_forge.core.job import create_job
from avatar_forge.core.runner import StageFailedError, run_job


def _run_ingest(source: Path, jobs_dir: Path) -> tuple[Path, dict]:
    job = create_job(
        {"front": source},
        adult_confirmed=True,
        consent_confirmed=True,
        root=jobs_dir,
    )
    results = run_job(job, load_pipeline_config(), to_stage="s00_ingest")
    return job, results["s00_ingest"].data["views"]["front"]


def test_exif_orientation_is_applied(tmp_path: Path, jobs_dir: Path) -> None:
    source = tmp_path / "oriented.jpg"
    image = Image.new("RGB", (1000, 600))
    exif = image.getexif()
    exif[0x0112] = 6
    image.save(source, exif=exif)

    job, data = _run_ingest(source, jobs_dir)

    with Image.open(job / "s00_ingest" / "front.png") as output:
        assert output.size == (600, 1000)
    assert data["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()


def test_large_image_is_downscaled(tmp_path: Path, jobs_dir: Path) -> None:
    source = tmp_path / "large.png"
    Image.new("RGB", (5000, 3000)).save(source)

    job, data = _run_ingest(source, jobs_dir)
    max_long_side = load_pipeline_config()["stages"]["s00_ingest"][
        "max_long_side_px"
    ]

    with Image.open(job / "s00_ingest" / "front.png") as output:
        assert max(output.size) == max_long_side
    assert data["downscaled"] is True


def test_alpha_image_stays_rgba(
    tmp_path: Path, jobs_dir: Path, front_image: Path
) -> None:
    source = tmp_path / "alpha.png"
    with Image.open(front_image) as image:
        image.convert("RGBA").save(source)

    job, _ = _run_ingest(source, jobs_dir)

    with Image.open(job / "s00_ingest" / "front.png") as output:
        assert output.mode == "RGBA"


def test_corrupt_image_fails(tmp_path: Path, jobs_dir: Path) -> None:
    source = tmp_path / "x.jpg"
    source.write_bytes(b"not an image")
    job = create_job(
        {"front": source},
        adult_confirmed=True,
        consent_confirmed=True,
        root=jobs_dir,
    )

    with pytest.raises(StageFailedError):
        run_job(job, load_pipeline_config(), to_stage="s00_ingest")
