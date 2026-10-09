from __future__ import annotations

import argparse
import importlib
import json
import logging
import pkgutil
import time
from pathlib import Path
from typing import Any

from avatar_forge.models.base import model_entry, reset_vram_peak, vram_peak_gb
from avatar_forge.models.trials import REGISTRY, TrialSkippedError

LOGGER = logging.getLogger(__name__)


def _load_trial_adapters() -> None:
    from avatar_forge import models

    adapter_names = sorted(
        module.name
        for module in pkgutil.iter_modules(models.__path__)
        if module.name.startswith("trial_adapters_")
    )
    if not adapter_names:
        LOGGER.warning("No trial adapter modules are installed yet")
        return

    for module_name in adapter_names:
        importlib.import_module(f"avatar_forge.models.{module_name}")


def _expand_images(image_patterns: list[str]) -> list[Path]:
    images: dict[Path, None] = {}
    for pattern in image_patterns:
        candidate = Path(pattern)
        matches = sorted(candidate.parent.glob(candidate.name)) if any(
            character in pattern for character in "*?["
        ) else ([candidate] if candidate.is_file() else [])
        for image in matches:
            if image.is_file():
                images[image] = None
    return list(images)


def _run_trial(
    role: str,
    name: str,
    image_path: Path,
    out_root: Path,
) -> dict[str, Any]:
    out_dir = out_root / role / name / image_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    trial_fn = REGISTRY[(role, name)]

    # Written first so a stalled or killed run still leaves an explicit failure record (E-011).
    _write_json(out_dir / "trial.json", {
        "role": role,
        "name": name,
        "image": str(image_path),
        "ok": False,
        "seconds": 0.0,
        "vram_peak_gb": 0.0,
        "error": "incomplete: process ended before this image finished (stall or kill)",
        "skipped": False,
        "extra": {},
    })
    reset_vram_peak()
    started_at = time.perf_counter()
    error: str | None = None
    skipped = False
    extra: dict[str, Any] = {}
    try:
        extra = trial_fn(model_entry(role, name), image_path, out_dir)
        if not isinstance(extra, dict):
            raise TypeError("TrialFn must return a dict")
    except TrialSkippedError as exc:
        error = str(exc)
        skipped = True
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        LOGGER.exception("Trial failed for %s/%s on %s", role, name, image_path)

    seconds = time.perf_counter() - started_at
    result = {
        "role": role,
        "name": name,
        "image": str(image_path),
        "ok": error is None,
        "skipped": skipped,
        "seconds": seconds,
        "vram_peak_gb": vram_peak_gb(),
        "error": error,
        "extra": extra,
    }
    _write_json(out_dir / "trial.json", result)
    return result


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2)
        json_file.write("\n")


def _write_summary(
    role: str,
    name: str,
    results: list[dict[str, Any]],
    out_root: Path,
) -> None:
    durations = [float(result["seconds"]) for result in results]
    summary = {
        "role": role,
        "name": name,
        "total": len(results),
        "ok": sum(bool(result["ok"]) for result in results),
        "failed": sum(
            not bool(result["ok"]) and not bool(result.get("skipped"))
            for result in results
        ),
        "skipped": sum(bool(result.get("skipped")) for result in results),
        "mean_seconds": sum(durations) / len(durations) if durations else 0.0,
        "max_vram_gb": max(
            (float(result["vram_peak_gb"]) for result in results), default=0.0
        ),
    }
    summary_path = out_root / role / name / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2)
        summary_file.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run registered model trials")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--all-registered", action="store_true")
    selection.add_argument("--role")
    parser.add_argument("--name")
    parser.add_argument("--images", nargs="+", required=True)
    parser.add_argument("--out-root", type=Path, default=Path("jobs/_model_trials"))
    args = parser.parse_args(argv)

    if not args.all_registered and (not args.role or not args.name):
        parser.error("provide --role and --name, or use --all-registered")

    _load_trial_adapters()
    if args.all_registered:
        selections = sorted(REGISTRY)
    else:
        selections = [(args.role, args.name)]
        if selections[0] not in REGISTRY:
            parser.error(f"no trial registered for {args.role!r}/{args.name!r}")

    images = _expand_images(args.images)
    if not images:
        parser.error("no input images matched --images")

    for role, name in selections:
        results: list[dict[str, Any]] = []
        for image_path in images:
            results.append(_run_trial(role, name, image_path, args.out_root))
            # Updated after every image so an interrupted run still appears in the report.
            _write_summary(role, name, results, args.out_root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
