"""s09_export — FBX + textures + import_manifest.json for UE5.

Implemented by task T26 (MVP fused export) and T38 (per-garment export).

Reads:   s06_garments (MVP) or s08_assemble/character.blend, s07_texture, s05_body_params
Writes:  s09_export/<job_id>/  layout in docs/03_UE5_INTEGRATION.md §1
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from jsonschema import ValidationError

from avatar_forge.blender_runner import run_blender
from avatar_forge.core import schemas
from avatar_forge.core.stage import StageContext, StageResult

BLENDER_DIR = Path(__file__).resolve().parents[1] / "blender"


def run(ctx: StageContext) -> StageResult:
    s06_mode = ctx.config["stages"]["s06_garments"]["mode"]
    if s06_mode == "separate":
        return StageResult.not_implemented("T38")

    job_id = ctx.manifest["job_id"]
    export_dir = ctx.stage_dir / job_id
    if export_dir.exists():
        shutil.rmtree(export_dir)
    export_dir.mkdir(parents=True)

    glb = ctx.previous_output("s06_garments", "fused/character_fused.glb")
    fbx = export_dir / "fused" / "character_fused.fbx"
    result = run_blender(
        BLENDER_DIR / "export_fbx.py",
        [
            "--in",
            str(glb),
            "--out-fbx",
            str(fbx),
            "--tex-dir",
            str(export_dir / "fused" / "textures"),
            "--id",
            "character_fused",
        ],
        ctx.config,
        log_path=ctx.job_dir / "logs" / "s09_export_fbx.blender.log",
    )
    stats_lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("EXPORT_STATS ")
    ]
    if not stats_lines:
        return StageResult(
            status="fail",
            messages=["export_fbx.py printed no EXPORT_STATS line"],
        )
    stats = json.loads(stats_lines[-1].split(" ", 1)[1])

    body_src = ctx.previous_output("s05_body_params", "body_params.json")
    body_dir = export_dir / "body"
    previews_dir = export_dir / "previews"
    body_dir.mkdir(parents=True)
    previews_dir.mkdir(parents=True)
    shutil.copyfile(body_src, body_dir / "body_params.json")
    shutil.copyfile(
        ctx.previous_output("s06_garments", "fused/front.png"),
        previews_dir / "front.png",
    )
    shutil.copyfile(
        ctx.previous_output("s06_garments", "fused/back.png"),
        previews_dir / "back.png",
    )
    body = json.loads((body_dir / "body_params.json").read_text(encoding="utf-8"))

    mesh: dict[str, object] = {
        "id": "character_fused",
        "kind": "fused",
        "path": "fused/character_fused.fbx",
    }
    textures = stats["textures"]
    if textures:
        mesh["material"] = {
            Path(name).stem.removeprefix("character_fused_"): f"fused/textures/{name}"
            for name in textures
        }
    import_manifest = {
        "schema_version": 1,
        "job_id": job_id,
        "body": body,
        "meshes": [mesh],
    }
    try:
        schemas.validate(import_manifest, "import_manifest.schema.json")
    except ValidationError as exc:
        return StageResult(
            status="fail",
            messages=[f"import_manifest.json failed schema validation: {exc.message}"],
        )
    manifest_path = export_dir / "import_manifest.json"
    manifest_path.write_text(
        json.dumps(import_manifest, indent=2) + "\n", encoding="utf-8"
    )

    written_files = sorted(
        path.relative_to(ctx.job_dir).as_posix()
        for path in export_dir.rglob("*")
        if path.is_file()
    )
    return StageResult(
        status="ok",
        outputs=written_files,
        data={
            "export_dir": export_dir.relative_to(ctx.job_dir).as_posix(),
            "fbx_mb": round(fbx.stat().st_size / 1e6, 2),
            "textures": len(textures),
        },
    )
