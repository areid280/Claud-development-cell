from __future__ import annotations

import copy
import importlib
import json
import logging
from pathlib import Path
from typing import Any

from avatar_forge.core import manifest as mf
from avatar_forge.core.log import add_file_handler, get_logger
from avatar_forge.core.stage import StageContext, StageResult
from avatar_forge.stages import STAGE_ORDER

log = get_logger(__name__)


class StageFailedError(RuntimeError):
    pass


def _select(from_stage: str | None, to_stage: str | None) -> list[str]:
    for name in (from_stage, to_stage):
        if name is not None and name not in STAGE_ORDER:
            raise ValueError(f"Unknown stage '{name}'. Stages: {', '.join(STAGE_ORDER)}")
    start = STAGE_ORDER.index(from_stage) if from_stage else 0
    end = STAGE_ORDER.index(to_stage) + 1 if to_stage else len(STAGE_ORDER)
    return list(STAGE_ORDER[start:end])


def run_stage(job_dir: Path, name: str, config: dict[str, Any], *, dry_run: bool) -> StageResult:
    manifest = mf.load(job_dir)
    stage_dir = job_dir / name
    stage_dir.mkdir(parents=True, exist_ok=True)
    stage_logger = get_logger(f"avatar_forge.stages.{name}")
    handler = add_file_handler(stage_logger, job_dir / "logs" / f"{name}.log")
    started = mf.now_iso()
    try:
        if dry_run:
            result = StageResult(status="skipped", messages=["dry run"])
        else:
            module = importlib.import_module(f"avatar_forge.stages.{name}")
            ctx = StageContext(
                name=name,
                job_dir=job_dir,
                stage_dir=stage_dir,
                config=config,
                manifest=copy.deepcopy(manifest),
                overrides=copy.deepcopy(manifest.get("overrides", {})),
                logger=stage_logger,
            )
            try:
                result = module.run(ctx)
            except Exception as exc:  # recorded in manifest, then re-raised as StageFailedError
                stage_logger.exception("stage crashed")
                result = StageResult(status="fail", messages=[f"{type(exc).__name__}: {exc}"])
    finally:
        stage_logger.removeHandler(handler)
        handler.close()

    manifest = mf.load(job_dir)
    manifest["stages"][name] = {
        "status": result.status,
        "started_at": started,
        "finished_at": mf.now_iso(),
        "outputs": result.outputs,
        "messages": result.messages,
        "data": result.data,
    }
    _sync_conventional_files(job_dir, manifest)
    mf.save(job_dir, manifest)
    return result


def _sync_conventional_files(job_dir: Path, manifest: dict[str, Any]) -> None:
    """Copy stage outputs with fixed names into the manifest (stages never edit it).

    - s05_body_params/body_params.json   -> manifest["body"]
    - s06_garments/*/garment.json        -> manifest["garments"] (sorted by id)
    Schema validation in mf.save() then checks these files for free.
    """
    body = job_dir / "s05_body_params" / "body_params.json"
    if body.exists():
        manifest["body"] = json.loads(body.read_text(encoding="utf-8"))
    garment_files = sorted((job_dir / "s06_garments").glob("*/garment.json"))
    if garment_files:
        manifest["garments"] = [json.loads(p.read_text(encoding="utf-8")) for p in garment_files]


def run_job(
    job_dir: Path,
    config: dict[str, Any],
    *,
    from_stage: str | None = None,
    to_stage: str | None = None,
    dry_run: bool = False,
) -> dict[str, StageResult]:
    """Run stages in order. Stops at the first 'fail'."""
    results: dict[str, StageResult] = {}
    for name in _select(from_stage, to_stage):
        log.info("stage %s: starting", name)
        result = run_stage(job_dir, name, config, dry_run=dry_run)
        results[name] = result
        level = logging.ERROR if result.status == "fail" else logging.INFO
        log.log(level, "stage %s: %s %s", name, result.status, "; ".join(result.messages))
        if result.status == "fail":
            raise StageFailedError(f"{name} failed: {'; '.join(result.messages)}")
    return results
