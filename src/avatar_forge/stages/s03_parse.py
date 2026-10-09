"""s03_parse — split each view into labelled part masks.

Implemented by task T22.

Reads:   s02_prepare/<view>_rgba.png
Writes:  s03_parse/<view>/<part>_mask.png   one binary mask per part
         s03_parse/parts.json               list of parts with label, view, area, bbox
Labels:  see config/pipeline.yaml -> stages.s03_parse.labels
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from PIL import Image

from avatar_forge.core.stage import StageContext, StageResult
from avatar_forge.models.registry import load_selected
from avatar_forge.parts import LABEL_COLORS
from avatar_forge.stages.parse_post import postprocess_masks


def run(ctx: StageContext) -> StageResult:
    cfg = ctx.stage_config()
    labels = [str(label) for label in cfg["labels"]]
    label_set = set(labels)
    min_area = int(cfg["min_part_area_px"])
    ctx.stage_dir.mkdir(parents=True, exist_ok=True)

    parts: list[dict[str, Any]] = []
    outputs: list[str] = []
    view_labels: dict[str, list[str]] = {}
    failed_views: list[str] = []

    with load_selected("parsing") as model:
        for item in ctx.manifest["inputs"]:
            view = str(item["view"])
            input_path = ctx.previous_output("s02_prepare", f"{view}_rgba.png")
            view_dir = ctx.stage_dir / view
            view_dir.mkdir(parents=True, exist_ok=True)

            with Image.open(input_path) as opened_image:
                image = opened_image.convert("RGBA")
                alpha = np.asarray(image.getchannel("A")) > 0
                predicted_masks = model.predict(image)

            canonical_masks: dict[str, np.ndarray] = {}
            for raw_label, raw_mask in predicted_masks.items():
                label = str(raw_label)
                if label == "background":
                    continue
                canonical_label = label if label in label_set else "accessory"
                if canonical_label == "background" or canonical_label not in label_set:
                    continue

                mask = np.asarray(raw_mask, dtype=bool)
                if mask.shape != alpha.shape:
                    raise ValueError(
                        f"{view}: mask for {label!r} has shape {mask.shape}; "
                        f"expected {alpha.shape}"
                    )
                if canonical_label in canonical_masks:
                    canonical_masks[canonical_label] |= mask
                else:
                    canonical_masks[canonical_label] = mask.copy()

            processed = postprocess_masks(canonical_masks, alpha, min_area)
            preview = np.zeros((*alpha.shape, 3), dtype=np.uint8)
            present_labels: list[str] = []
            for label in labels:
                if label == "background" or label not in processed:
                    continue
                mask, instances = processed[label]
                mask_path = view_dir / f"{label}_mask.png"
                Image.fromarray(mask.astype(np.uint8) * 255).save(mask_path)
                relative_mask_path = mask_path.relative_to(ctx.job_dir).as_posix()
                outputs.append(relative_mask_path)
                present_labels.append(label)

                ys, xs = np.nonzero(mask)
                area_px = int(mask.sum())
                parts.append(
                    {
                        "label": label,
                        "view": view,
                        "mask": relative_mask_path,
                        "area_px": area_px,
                        "bbox": [
                            int(xs.min()),
                            int(ys.min()),
                            int(xs.max()) + 1,
                            int(ys.max()) + 1,
                        ],
                        "instances": instances,
                    }
                )
                preview[mask] = LABEL_COLORS[label]

            preview_path = view_dir / "labels_preview.png"
            Image.fromarray(preview).save(preview_path)
            outputs.append(preview_path.relative_to(ctx.job_dir).as_posix())
            view_labels[view] = present_labels
            if not present_labels:
                failed_views.append(view)

    parts_path = ctx.stage_dir / "parts.json"
    parts_path.write_text(json.dumps(parts, indent=2) + "\n", encoding="utf-8")
    outputs.append(parts_path.relative_to(ctx.job_dir).as_posix())

    if failed_views:
        return StageResult(
            status="fail",
            outputs=outputs,
            messages=[f"{view}: no body parts found" for view in failed_views],
            data={"views": view_labels},
        )
    return StageResult(status="ok", outputs=outputs, data={"views": view_labels})
