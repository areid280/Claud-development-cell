from __future__ import annotations

from pathlib import Path

from avatar_forge.cli import main


def test_doctor_runs(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["doctor"]) == 0
    assert "avatar-forge" in capsys.readouterr().out


def test_run_refuses_without_consent(front_image: Path, jobs_dir: Path) -> None:
    assert main(["run", str(front_image), "--jobs-dir", str(jobs_dir), "--dry-run"]) == 3
    assert list(jobs_dir.iterdir()) == []


def test_run_dry_run_with_overrides(front_image: Path, jobs_dir: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    code = main([
        "run", str(front_image), "--jobs-dir", str(jobs_dir), "--dry-run",
        "--confirm-adult-consent", "--set", "height=172", "--set", "bust=+5%",
    ])
    assert code == 0
    job = next(jobs_dir.iterdir())
    assert main(["validate-manifest", str(job)]) == 0
    assert '"bust": "+5%"' in (job / "manifest.json").read_text()
