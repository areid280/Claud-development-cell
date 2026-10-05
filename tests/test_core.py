from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from avatar_forge.core import manifest as mf
from avatar_forge.core.config import deep_merge, load_pipeline_config, selected_model
from avatar_forge.core.job import ConsentError, create_job
from avatar_forge.core.runner import run_job
from avatar_forge.stages import STAGE_ORDER


def test_pipeline_config_loads() -> None:
    cfg = load_pipeline_config()
    assert "s01_validate" in cfg["stages"]
    assert cfg["stages"]["s01_validate"]["min_long_side_px"] >= 512


def test_deep_merge_overrides_nested() -> None:
    base = {"a": {"b": 1, "c": 2}, "d": 3}
    assert deep_merge(base, {"a": {"b": 9}}) == {"a": {"b": 9, "c": 2}, "d": 3}
    assert base["a"]["b"] == 1  # unchanged


def test_selected_model_requires_gate() -> None:
    with pytest.raises((LookupError, PermissionError)):
        selected_model("pose")


def test_create_job_requires_consent(front_image: Path, jobs_dir: Path) -> None:
    with pytest.raises(ConsentError):
        create_job({"front": front_image}, adult_confirmed=True, consent_confirmed=False,
                   root=jobs_dir)


def test_create_job_requires_front(front_image: Path, jobs_dir: Path) -> None:
    with pytest.raises(ValueError):
        create_job({"back": front_image}, adult_confirmed=True, consent_confirmed=True,
                   root=jobs_dir)


def test_create_job_writes_valid_manifest(front_image: Path, jobs_dir: Path) -> None:
    job = create_job({"front": front_image}, adult_confirmed=True, consent_confirmed=True,
                     root=jobs_dir)
    manifest = mf.load(job)
    mf.validate(manifest)
    assert manifest["inputs"][0]["view"] == "front"
    assert (job / manifest["inputs"][0]["path"]).is_file()


def test_manifest_rejects_bad_status(front_image: Path, jobs_dir: Path) -> None:
    job = create_job({"front": front_image}, adult_confirmed=True, consent_confirmed=True,
                     root=jobs_dir)
    manifest = mf.load(job)
    manifest["stages"]["s00_ingest"] = {
        "status": "great", "started_at": "", "finished_at": "",
        "outputs": [], "messages": [], "data": {},
    }
    with pytest.raises(jsonschema.ValidationError):
        mf.validate(manifest)


def test_dry_run_records_every_stage(front_image: Path, jobs_dir: Path) -> None:
    job = create_job({"front": front_image}, adult_confirmed=True, consent_confirmed=True,
                     root=jobs_dir)
    results = run_job(job, load_pipeline_config(), dry_run=True)
    assert list(results) == list(STAGE_ORDER)
    manifest = mf.load(job)
    assert set(manifest["stages"]) == set(STAGE_ORDER)


def test_real_run_with_stubs_does_not_fail(front_image: Path, jobs_dir: Path) -> None:
    """Unimplemented stages return 'skipped'; implemented ones must not fail on plumbing input."""
    job = create_job({"front": front_image}, adult_confirmed=True, consent_confirmed=True,
                     root=jobs_dir)
    results = run_job(job, load_pipeline_config(), to_stage="s00_ingest")
    assert results["s00_ingest"].status in {"ok", "warn", "skipped"}
    assert (job / "logs" / "s00_ingest.log").exists()


def test_body_params_file_synced_into_manifest(front_image: Path, jobs_dir: Path) -> None:
    job = create_job({"front": front_image}, adult_confirmed=True, consent_confirmed=True,
                     root=jobs_dir)
    body = {
        "units": "cm", "source": "test",
        "measurements": {"height": 170, "bust": 90, "underbust": 75, "waist": 66,
                         "hips": 95, "shoulder_width": 38, "inseam": 78},
        "colors": {"skin": "#e0b8a0", "hair": "#1c1a1f", "eyes": "#5a7a8c"},
    }
    (job / "s05_body_params").mkdir()
    (job / "s05_body_params" / "body_params.json").write_text(json.dumps(body))
    run_job(job, load_pipeline_config(), from_stage="s05_body_params", to_stage="s05_body_params")
    assert mf.load(job)["body"]["measurements"]["height"] == 170


def test_unknown_stage_rejected(front_image: Path, jobs_dir: Path) -> None:
    job = create_job({"front": front_image}, adult_confirmed=True, consent_confirmed=True,
                     root=jobs_dir)
    with pytest.raises(ValueError):
        run_job(job, load_pipeline_config(), from_stage="s99_nope")
