from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _markdown_path(path: Path, report_dir: Path) -> str:
    return path.relative_to(report_dir).as_posix()


def build_report(out_root: Path) -> str:
    by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    image_outputs: dict[tuple[str, str, str], list[Path]] = defaultdict(list)

    for summary_path in sorted(out_root.glob("*/*/summary.json")):
        with summary_path.open(encoding="utf-8") as summary_file:
            summary = json.load(summary_file)
        by_role[str(summary["role"])].append(summary)

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
                "| Name | OK / total | Mean s | Max VRAM GB |",
                "|---|---:|---:|---:|",
            ]
        )
        role_summaries = sorted(by_role[role], key=lambda summary: str(summary["name"]))
        for summary in role_summaries:
            lines.append(
                f"| {summary['name']} | {summary['ok']} / {summary['total']} | "
                f"{float(summary['mean_seconds']):.3f} | "
                f"{float(summary['max_vram_gb']):.3f} |"
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
