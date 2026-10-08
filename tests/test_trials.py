from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts import trial_model

from avatar_forge.models.trials import register


def test_trial_model_main_writes_trial_and_summary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    image_path = tmp_path / "synthetic.png"
    image_path.write_bytes(b"synthetic image")
    out_root = tmp_path / "trials"

    @register("test", "fake")
    def fake_trial(entry: dict[str, Any], image: Path, out_dir: Path) -> dict[str, Any]:
        assert entry == {"name": "fake"}
        assert image == image_path
        assert out_dir.is_dir()
        return {"result": "ok"}

    monkeypatch.setattr(trial_model, "_load_trial_adapters", lambda: None)
    monkeypatch.setattr(
        trial_model, "model_entry", lambda role, name: {"name": name}
    )

    assert trial_model.main(
        [
            "--role",
            "test",
            "--name",
            "fake",
            "--images",
            str(image_path),
            "--out-root",
            str(out_root),
        ]
    ) == 0

    trial_path = out_root / "test" / "fake" / "synthetic" / "trial.json"
    summary_path = out_root / "test" / "fake" / "summary.json"
    trial = json.loads(trial_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert trial["ok"] is True
    assert trial["extra"] == {"result": "ok"}
    assert trial["error"] is None
    assert summary["total"] == 1
    assert summary["ok"] == 1
    assert summary["failed"] == 0


def test_trial_record_marks_interrupted_image_as_failed(tmp_path: Path, monkeypatch: Any) -> None:
    from avatar_forge.models.trials import REGISTRY

    seen: dict[str, object] = {}

    def fake_trial(entry: dict, image_path: Path, out_dir: Path) -> dict:
        seen.update(json.loads((out_dir / "trial.json").read_text(encoding="utf-8")))
        return {}

    monkeypatch.setitem(REGISTRY, ("test", "interrupt"), fake_trial)
    monkeypatch.setattr(trial_model, "model_entry", lambda role, name: {})
    image = tmp_path / "x.png"
    image.write_bytes(b"")

    trial_model._run_trial("test", "interrupt", image, tmp_path / "out")

    assert seen["ok"] is False and str(seen["error"]).startswith("incomplete")
