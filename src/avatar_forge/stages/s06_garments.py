"""s06_garments — one mesh per garment.

MVP (task T25): mode "mvp_fused" builds a single fused mesh of the whole figure.
M3 (tasks T30–T35): mode "separate" classifies each garment and uses its strategy
(skin_layer / template / generated).

Reads:   s02_prepare/front_rgba.png, s05_body_params/body_params.json
Writes:  s06_garments/fused/{raw.glb, character_fused.glb, front.png, back.png} (mvp_fused)
"""

from __future__ import annotations

import json
from pathlib import Path

import trimesh
from PIL import Image

from avatar_forge.blender_runner import run_blender
from avatar_forge.core.stage import StageContext, StageResult
from avatar_forge.models.base import reset_vram_peak, vram_peak_gb
from avatar_forge.models.registry import load_selected

BLENDER_DIR = Path(__file__).resolve().parents[1] / "blender"


def run(ctx: StageContext) -> StageResult:
    cfg = ctx.stage_config()
    mode = cfg["mode"]
    if mode == "separate":
        return StageResult.not_implemented("T30")
    if mode != "mvp_fused":
        return StageResult(
            status="fail",
            messages=[f"Unknown s06_garments mode '{mode}'"],
        )

    body_path = ctx.previous_output("s05_body_params", "body_params.json")
    body = json.loads(body_path.read_text(encoding="utf-8"))
    height_m = body["measurements"]["height"] / 100.0
    rgba_path = ctx.previous_output("s02_prepare", "front_rgba.png")
    with Image.open(rgba_path) as image:
        rgba = image.convert("RGBA")

    fused = ctx.stage_dir / "fused"
    fused.mkdir(parents=True, exist_ok=True)

    reset_vram_peak()
    with load_selected("image_to_3d") as model:
        name = model.name
        raw = model.predict(
            rgba,
            out_dir=fused,
            seed=int(cfg["mvp_seed"]),
            output_name="raw.glb",
        )
        vram = vram_peak_gb()
    ctx.logger.info("s06_garments model=%s vram_peak_gb=%.2f", name, vram)

    out = fused / "character_fused.glb"
    cleanup_result = run_blender(
        BLENDER_DIR / "cleanup_mesh.py",
        [
            "--in",
            str(raw),
            "--out",
            str(out),
            "--height-m",
            f"{height_m:.4f}",
            "--max-tris",
            str(cfg["mvp_max_triangles"]),
            "--merge-dist",
            str(cfg["mvp_merge_distance_m"]),
            "--min-part-frac",
            str(cfg["mvp_min_part_fraction"]),
            "--color-space",
            str(cfg["mvp_color_space"]),
        ],
        ctx.config,
        log_path=ctx.job_dir / "logs" / "s06_garments_cleanup.blender.log",
    )
    stats_lines = [
        line
        for line in cleanup_result.stdout.splitlines()
        if line.startswith("CLEANUP_STATS ")
    ]
    if not stats_lines:
        return StageResult(
            status="fail",
            messages=["cleanup_mesh.py printed no CLEANUP_STATS line"],
        )
    stats = json.loads(stats_lines[-1].split(" ", 1)[1])

    run_blender(
        BLENDER_DIR / "render_previews.py",
        ["--in", str(out), "--out-dir", str(fused), "--size", str(cfg["mvp_preview_px"])],
        ctx.config,
        log_path=ctx.job_dir / "logs" / "s06_garments_previews.blender.log",
    )
    mesh = trimesh.load(out, force="mesh")
    mesh.merge_vertices(merge_tex=True, merge_norm=True)

    outputs = [
        raw,
        out,
        fused / "front.png",
        fused / "back.png",
    ]
    return StageResult(
        status="ok",
        outputs=[path.relative_to(ctx.job_dir).as_posix() for path in outputs],
        data={
            "model": name,
            "triangles": len(mesh.faces),
            "triangles_raw": stats["triangles_in"],
            "parts_removed": stats["parts_removed"],
            "watertight": bool(mesh.is_watertight),
            "height_m": round(height_m, 4),
            "vram_peak_gb": round(vram, 2),
        },
    )
