# T26 — Stage s09_export + UE5 import script
milestone: M2 · effort: medium · depends: T25
owner input: run the UE5 script on your PC and paste the Output Log (card stays `waiting-owner` until then)

> **Opus pre-work (2026-10-10, after E-023/E-024/E-025):** `src/avatar_forge/blender/export_fbx.py` and
> `tests/test_export_fbx.py` are **done and tested** (Blender 4.2: height and sRGB vertex colours survive
> GLB → FBX; textures are saved per socket). `avatar_forge.core.schemas.validate()` resolves the
> `body_params` `$ref` inside `import_manifest.schema.json`. This card is now: the stage glue, the UE script,
> their tests, and the owner's UE run.

## Goal
An export folder UE5 can import with one script.

## Read first
- docs/06_STAGE_CONTRACTS.md (§4: `schemas.validate`, copy only with `shutil.copyfile`)
- src/avatar_forge/stages/s09_export.py (stub)
- src/avatar_forge/stages/s06_garments.py (the pattern: `run_blender`, parsing a `*_STATS` line, fakes in tests)
- src/avatar_forge/blender/export_fbx.py (done; read its docstring and arguments only)
- schemas/import_manifest.schema.json
- docs/03_UE5_INTEGRATION.md §1–2
- unreal/import_character.py (stub)
- tests/test_s06_garments.py (pattern for faking `run_blender`)

## Contracts (Opus, D-015)
- The fused MVP mesh has vertex colours and no textures, so `fused/textures/` stays empty.
- `import_manifest.json` has one mesh `{"id": "character_fused", "kind": "fused", "path": "fused/character_fused.fbx"}`
  and **no `material` key** (allowed by the schema). Any mesh without `material.basecolor` uses
  `/Game/AvatarForge/M_AF_VertexColor` in UE.

## Do — part A: `run(ctx)` in `src/avatar_forge/stages/s09_export.py`
1. `s06_mode = ctx.config["stages"]["s06_garments"]["mode"]`; if it is `"separate"` return
   `StageResult.not_implemented("T38")`.
2. `job_id = ctx.manifest["job_id"]`; `export_dir = ctx.stage_dir / job_id`. If it exists,
   `shutil.rmtree(export_dir)` first (a rerun must not keep stale files). Then create it.
3. `glb = ctx.previous_output("s06_garments", "fused/character_fused.glb")`.
4. `result = run_blender(BLENDER_DIR / "export_fbx.py", ["--in", str(glb), "--out-fbx", str(export_dir / "fused" / "character_fused.fbx"), "--tex-dir", str(export_dir / "fused" / "textures"), "--id", "character_fused"], ctx.config, log_path=ctx.job_dir / "logs" / "s09_export_fbx.blender.log")`
   with `BLENDER_DIR` as in s06. Parse the **last** line starting `"EXPORT_STATS "`; none →
   `fail` with `"export_fbx.py printed no EXPORT_STATS line"`.
5. With `shutil.copyfile` only (E-025):
   `s05_body_params/body_params.json` → `export_dir/body/body_params.json`;
   `s06_garments/fused/front.png` and `back.png` → `export_dir/previews/` (use `ctx.previous_output`).
6. Build `import_manifest = {"schema_version": 1, "job_id": job_id, "body": <body_params dict>,
   "meshes": [{"id": "character_fused", "kind": "fused", "path": "fused/character_fused.fbx"}]}`.
   If `stats["textures"]` is not empty (not expected in M2), add
   `"material": {suffix: f"fused/textures/{name}"}` where `suffix` is the part after `character_fused_`
   without `.png` (`basecolor`, `normal`, `roughness`, `metallic`).
   `schemas.validate(import_manifest, "import_manifest.schema.json")`; on `jsonschema.ValidationError`
   return `fail` with `f"import_manifest.json failed schema validation: {exc.message}"`.
   Write `export_dir / "import_manifest.json"` (indent 2, trailing newline).
7. Return `StageResult(status="ok", outputs=[every file written, relative posix, sorted],
   data={"export_dir": export_dir.relative_to(ctx.job_dir).as_posix(), "fbx_mb": round(size / 1e6, 2), "textures": len(stats["textures"])})`.

## Do — part B: `unreal/import_character.py` (UE 5.6 Python; only `unreal` + standard library)
Keep `import unreal` **inside functions** so tests can import the file without Unreal.
1. Pure, tested function:
   ```python
   def plan_import(manifest: dict, export_dir: Path) -> list[dict]:
       """One entry per mesh: {"fbx": abs path str, "destination": "/Game/AvatarForge/<job_id>",
       "asset_name": <id>, "material": "vertex_color" | "garment", "textures": {suffix: abs path str}}"""
   ```
   `"material"` is `"garment"` only when the mesh has `material.basecolor`; otherwise `"vertex_color"`.
2. Manifest path: env `AF_IMPORT_MANIFEST`; else the first line of `import_manifest_path.txt` next to this
   script (owner pastes the path there); else try `tkinter.filedialog.askopenfilename` inside `try/except`;
   else `unreal.log_error("Set AF_IMPORT_MANIFEST or import_manifest_path.txt")` and return.
3. `ensure_vertex_color_material()` → `/Game/AvatarForge/M_AF_VertexColor` if missing:
   `asset_tools = unreal.AssetToolsHelpers.get_asset_tools()`;
   `mat = asset_tools.create_asset("M_AF_VertexColor", "/Game/AvatarForge", unreal.Material, unreal.MaterialFactoryNew())`;
   `mel = unreal.MaterialEditingLibrary`;
   `vc = mel.create_material_expression(mat, unreal.MaterialExpressionVertexColor, -400, 0)`;
   `mel.connect_material_property(vc, "", unreal.MaterialProperty.MP_BASE_COLOR)`;
   `rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)`;
   `rough.set_editor_property("r", 0.6)`; `mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)`;
   `mel.recompile_material(mat)`; `unreal.EditorAssetLibrary.save_asset(mat.get_path_name())`.
   Check existence first with `unreal.EditorAssetLibrary.does_asset_exist(...)`.
4. `ensure_garment_material()` (`M_AF_Garment` with TextureSampleParameter2D `BaseColor`, `Normal`
   (sampler type normal), `Roughness`, `Metallic`) is called **only if** some plan entry has
   `"material": "garment"`. M2 never calls it, so the owner's first run cannot fail there.
5. Import each entry: `task = unreal.AssetImportTask()`; set `filename`, `destination_path`,
   `destination_name = asset_name`, `automated = True`, `save = True`, `replace_existing = True`;
   `ui = unreal.FbxImportUI()`; `ui.import_mesh = True`; `ui.import_as_skeletal = False`;
   `ui.import_materials = False`; `ui.import_textures = False`; `ui.import_animations = False`;
   `ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH`;
   `ui.static_mesh_import_data.set_editor_property("vertex_color_import_option", unreal.VertexColorImportOption.REPLACE)`;
   `ui.static_mesh_import_data.set_editor_property("combine_meshes", True)`; `task.options = ui`;
   `asset_tools.import_asset_tasks([task])`; paths = `task.get_editor_property("imported_object_paths")`.
   For `"vertex_color"`: `mesh = unreal.EditorAssetLibrary.load_asset(path)`; `mesh.set_material(0, unreal.EditorAssetLibrary.load_asset("/Game/AvatarForge/M_AF_VertexColor"))`; save it.
6. `unreal.log` each imported asset path, then the body: height and every measurement in cm, and the
   three colours, one per line, prefixed `AvatarForge:`.

## Tests
`tests/test_s09_export.py` (hand-built `StageContext`, `config=load_pipeline_config()`, manifest
`{"job_id": "20261010-000000-abcdef"}`; write s05 `body_params.json` (valid per schema), s06
`fused/character_fused.glb` (any bytes for the fake case), `front.png`, `back.png`):
1. Fake `run_blender` (writes a dummy FBX at `--out-fbx`, stdout `EXPORT_STATS {"meshes": 1, "textures": [], "color_attributes": ["Color"]}`):
   status `ok`; files exist at the §1 layout of docs/03; `import_manifest.json` validates with
   `schemas.validate` and has no `material`; outputs sorted and relative.
2. A stale file inside `export_dir` from a previous run is gone after `run`.
3. No stats line → `fail` with the exact message.
4. s06 mode `separate` → `skipped`.
5. `@pytest.mark.blender`: real Blender, a small vertex-coloured GLB (trimesh box with `ColorVisuals`) →
   the FBX exists and is larger than 1 kB.

`tests/test_unreal_plan.py`: load `unreal/import_character.py` with `importlib.util.spec_from_file_location`
(no `unreal` module available); `plan_import` for the fused manifest gives one entry with
`"material": "vertex_color"` and destination `/Game/AvatarForge/<job_id>`; a manifest mesh with
`material.basecolor` gives `"garment"` and an absolute texture path.

## Verify
1. `ruff check src tests unreal` and `pytest -q` → paste the summary lines.
2. `avatar-forge rerun /workspace/jobs/20261010-104423-71096a --from s09_export --to s09_export`
   (s07/s08 are skipped stubs; `--from s09_export` runs only this stage) → paste the stage line, and
   `find /workspace/jobs/20261010-104423-71096a/s09_export -type f | sort` and `ls -la` of the FBX.
3. Set this card to `waiting-owner` in STATUS.md, commit `T26: <summary> (awaiting UE run)` and push. Tell the
   owner: download `s09_export/20261010-104423-71096a/` (VS Code Explorer → right-click → Download), follow
   docs/03 §2, put the downloaded `import_manifest.json` path in `import_manifest_path.txt` next to the
   script, run it, and paste the Output Log lines containing `AvatarForge` or `Error`.
4. When the owner pastes the log: fix only errors it shows, then set `done`.

## Log
