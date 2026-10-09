"""s01_validate — check inputs meet the rules in docs/00_PROJECT_BRIEF.md §4.

Implemented by task T20.

Reads:   s00_ingest/<view>.png
Writes:  s01_validate/report.json, s01_validate/<view>_keypoints.json
Status:  "fail" if any hard rule fails (with a clear human reason),
         "warn" for soft issues (e.g. crossed arms), else "ok".
Config:  config/pipeline.yaml -> stages.s01_validate
"""

from __future__ import annotations

import importlib
import json

from PIL import Image

from avatar_forge.core.config import selected_model
from avatar_forge.core.stage import StageContext, StageResult
from avatar_forge.models.base import ModelWrapper
from avatar_forge.stages.validate_rules import evaluate


def _wrapper_for_entry(entry: dict) -> type[ModelWrapper]:
    role = "pose"
    module_name = (
        f"avatar_forge.models.{role}_"
        f"{entry['name'].replace('-', '_').replace('.', '_')}"
    )
    module = importlib.import_module(module_name)
    for attr in vars(module).values():
        if (
            isinstance(attr, type)
            and issubclass(attr, ModelWrapper)
            and getattr(attr, "role", None) == role
        ):
            return attr
    raise LookupError(f"No pose wrapper found for {entry['name']!r}")


def run(ctx: StageContext) -> StageResult:
    cfg = ctx.stage_config()
    report: dict[str, dict[str, object]] = {}
    outputs: list[str] = []
    overall_status = "ok"
    messages: list[str] = []

    ctx.stage_dir.mkdir(parents=True, exist_ok=True)
    entry = selected_model("pose")
    wrapper_class = _wrapper_for_entry(entry)

    with wrapper_class(entry) as model:
        for item in ctx.manifest.get("inputs", []):
            view = str(item["view"])
            source = ctx.job_dir / "s00_ingest" / f"{view}.png"
            persons: list[dict] = []
            if not source.exists():
                status = "fail"
                view_messages = [f"Missing input image for {view}."]
            else:
                with Image.open(source) as image:
                    image_size = image.size
                    persons = model.predict(image)
                status, view_messages = evaluate(persons, image_size, cfg)

            report[view] = {"status": status, "messages": view_messages}
            keypoints_path = ctx.stage_dir / f"{view}_keypoints.json"
            keypoints_path.write_text(json.dumps(persons, indent=2), encoding="utf-8")
            outputs.append(keypoints_path.relative_to(ctx.job_dir).as_posix())

            status_rank = {"ok": 0, "warn": 1, "fail": 2}
            if status_rank[status] > status_rank.get(overall_status, 0):
                overall_status = status
            messages.extend(f"{view}: {message}" for message in view_messages)

    report_path = ctx.stage_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    outputs.append(report_path.relative_to(ctx.job_dir).as_posix())

    return StageResult(
        status=overall_status,
        outputs=outputs,
        messages=messages,
        data={"views": report},
    )
