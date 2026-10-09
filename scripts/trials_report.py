from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from avatar_forge.core.config import load_yaml
from avatar_forge.core.paths import REPO_ROOT

REFERENCE_PATH = REPO_ROOT / "samples" / "reference.yaml"


def _markdown_path(path: Path, report_dir: Path) -> str:
    return path.relative_to(report_dir).as_posix()


def _measurement_error_lines(out_root: Path, references: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for trial_path in sorted(out_root.glob("body_measure/*/*/trial.json")):
        with trial_path.open(encoding="utf-8") as trial_file:
            trial = json.load(trial_file)
        sample_name = Path(str(trial["image"])).stem
        reference = references.get(sample_name)
        measurements_path = trial_path.parent / "measurements.json"
        if not reference or not measurements_path.is_file():
            continue
        with measurements_path.open(encoding="utf-8") as measurements_file:
            output = json.load(measurements_file)
        measurements = output.get("measurements", output)
        for measurement, expected in reference.items():
            predicted = measurements.get(measurement)
            if predicted is None or float(expected) == 0:
                continue
            error_percent = abs(float(predicted) - float(expected)) / abs(
                float(expected)
            ) * 100
            lines.append(
                f"| `{sample_name}` | {measurement} | {float(expected):.2f} | "
                f"{float(predicted):.2f} | {error_percent:.2f}% |"
            )
    return lines


def _candidate_result(out_root: Path, role: str, name: str, summary: dict[str, Any]) -> str:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((out_root / role / name).glob("*/trial.json"))
    ]
    skipped = [trial for trial in trials if trial.get("skipped")]
    failed = [trial for trial in trials if not trial.get("ok") and not trial.get("skipped")]
    if skipped and not failed and not summary.get("ok"):
        return f"skipped: {skipped[0].get('error', 'no reason provided')}"
    if failed:
        return f"failed: {failed[0].get('error', 'unknown error')}"
    if summary.get("failed"):
        return "failed: no trial details recorded"
    if summary.get("ok"):
        return "ok"
    return "not run"


def build_report(out_root: Path, reference_path: Path | None = None) -> str:
    by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    image_outputs: dict[tuple[str, str, str], list[Path]] = defaultdict(list)

    if reference_path is None:
        reference_path = REFERENCE_PATH
    references = load_yaml(reference_path) if reference_path.is_file() else {}

    for summary_path in sorted(out_root.glob("*/*/summary.json")):
        with summary_path.open(encoding="utf-8") as summary_file:
            summary = json.load(summary_file)
        by_role[str(summary["role"])].append(summary)

    # A run killed before writing summary.json (E-011): rebuild the summary from trial.json files.
    for candidate_dir in sorted({path.parent.parent for path in out_root.glob("*/*/*/trial.json")}):
        if (candidate_dir / "summary.json").exists():
            continue
        trials = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(candidate_dir.glob("*/trial.json"))
        ]
        durations = [float(trial.get("seconds", 0.0)) for trial in trials]
        by_role[candidate_dir.parent.name].append({
            "role": candidate_dir.parent.name,
            "name": candidate_dir.name,
            "total": len(trials),
            "ok": sum(bool(trial.get("ok")) for trial in trials),
            "failed": sum(
                not bool(trial.get("ok")) and not bool(trial.get("skipped"))
                for trial in trials
            ),
            "skipped": sum(bool(trial.get("skipped")) for trial in trials),
            "mean_seconds": sum(durations) / len(durations) if durations else 0.0,
            "max_vram_gb": max(
                (float(trial.get("vram_peak_gb", 0.0)) for trial in trials), default=0.0
            ),
        })

    for trial_path in sorted(out_root.glob("*/*/*/trial.json")):
        with trial_path.open(encoding="utf-8") as trial_file:
            trial = json.load(trial_file)
        key = (str(trial["role"]), str(trial["name"]), str(trial["image"]))
        image_outputs[key].extend(sorted(trial_path.parent.rglob("*.png")))

    report_dir = out_root
    lines = ["# Model trial report", ""]
    for role in sorted(by_role):
        lines.extend(
            [
                f"## {role}",
                "",
                "| Name | OK / total | Mean s | Max VRAM GB | Result |",
                "|---|---:|---:|---:|---|",
            ]
        )
        role_summaries = sorted(by_role[role], key=lambda summary: str(summary["name"]))
        for summary in role_summaries:
            lines.append(
                f"| {summary['name']} | {summary['ok']} / {summary['total']} | "
                f"{float(summary['mean_seconds']):.3f} | "
                f"{float(summary['max_vram_gb']):.3f} | "
                f"{_candidate_result(out_root, role, str(summary['name']), summary)} |"
            )

        if role == "body_measure" and references:
            errors = _measurement_error_lines(out_root, references)
            lines.extend(
                [
                    "",
                    "Measurement errors vs owner references:",
                    "",
                    "| Image | Measurement | Reference cm | Result cm | Error |",
                    "|---|---|---:|---:|---:|",
                ]
            )
            lines.extend(
                errors or ["| No matching reference measurements | — | — | — | — |"]
            )

        lines.extend(["", "Output PNGs:", ""])
        for summary in role_summaries:
            name = str(summary["name"])
            for (image_role, image_name, image), paths in sorted(image_outputs.items()):
                if image_role != role or image_name != name:
                    continue
                image_label = Path(image).name
                if not paths:
                    lines.append(f"- `{name}` / `{image_label}`: no PNG outputs")
                    continue
                for path in paths:
                    relative_path = _markdown_path(path, report_dir)
                    lines.append(
                        f"- `{name}` / `{image_label}`: "
                        f"[{relative_path}]({relative_path})"
                    )
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a model trial report")
    parser.add_argument("--root", type=Path, default=Path("jobs/_model_trials"))
    args = parser.parse_args(argv)
    report_path = args.root / "REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(args.root), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
