# T28 — Front-photo texture projection (MVP)
milestone: M2 · effort: medium · depends: T26
(runs before T27, so the end-to-end evidence pack shows the textured result; the UE check of the textured
material happens in T27 step 3)

> **Why (Opus, D-016):** the fused TRELLIS mesh has the right shape but blurry colour and no usable face.
> This card paints the full-resolution front photo (`s02_prepare/front_rgba.png`, 2048 px tall) onto the
> camera-facing parts of the mesh and bakes one base-colour texture. Back and sides keep the vertex colours.
> The final face will still come from MetaHuman (D-016); this makes the MVP's front sharp now.
>
> **Already done by Opus (do not change):** `src/avatar_forge/blender/project_texture.py` and
> `tests/test_project_texture.py` (Blender 4.2: exact photo and mesh colours in the baked texture, hidden
> surfaces keep the mesh colour), the `project_*` / `mvp_texture` keys in `config/pipeline.yaml`,
> `scripts/preview_sheet.py --compare`. `s09_export` already turns a GLB texture into
> `material.basecolor` in `import_manifest.json` (T26). This card is the glue in s06, the UE material,
> their tests and the runs.

## Read first
- docs/06_STAGE_CONTRACTS.md
- src/avatar_forge/stages/s06_garments.py and tests/test_s06_garments.py (you extend both)
- src/avatar_forge/blender/project_texture.py (docstring and arguments only)
- config/pipeline.yaml (`stages.s06_garments`: `mvp_texture` and `project_*`; already added, do not edit)
- unreal/import_character.py and tests/test_unreal_plan.py (you extend both)
- docs/05_DECISIONS.md D-016

## Do — part A: `s06_garments.run` (mode `mvp_fused`)
1. Cleanup output name depends on `cfg["mvp_texture"]`:
   - `"vertex_colors"`: unchanged (cleanup writes `fused/character_fused.glb`).
   - `"project_front"`: cleanup writes `fused/character_vc.glb` instead; then
     ```python
     result = run_blender(
         BLENDER_DIR / "project_texture.py",
         ["--in", str(vc), "--image", str(ctx.previous_output("s02_prepare", "front_rgba.png")),
          "--out", str(out), "--tex-px", str(cfg["project_tex_px"]),
          "--facing-min", str(cfg["project_facing_min"]), "--facing-full", str(cfg["project_facing_full"]),
          "--erode-px", str(cfg["project_erode_px"]), "--margin-px", str(cfg["project_margin_px"])],
         ctx.config,
         log_path=ctx.job_dir / "logs" / "s06_garments_project.blender.log",
     )
     ```
     with `out = fused / "character_fused.glb"` (so s09 needs no change). Parse the last line starting
     `"PROJECT_STATS "`; none → `fail` with `"project_texture.py printed no PROJECT_STATS line"`.
   - Any other value → `fail` with `f"Unknown mvp_texture '{value}'"` (check before running the model).
2. Previews: always render the final `character_fused.glb` into `fused/` (front.png, back.png, as now).
   With `project_front`, also render `character_vc.glb` into `fused/vertex_colors/` (the before/after
   evidence). Use log names `s06_garments_previews.blender.log` and `s06_garments_previews_vc.blender.log`.
3. Outputs: add `fused/character_vc.glb`, `fused/vertex_colors/front.png` and `back.png` when projecting.
4. `data`: add `"texture": cfg["mvp_texture"]`; when projecting also `"coverage"`, `"hidden_vertices"` and
   `"project_seconds"` (= stats `seconds`) from the stats line.
5. If projecting and `stats["coverage"] < cfg["project_min_coverage"]`: status `"warn"` with message
   `f"Front photo may be misaligned with the mesh (coverage {c:.2f} < {m:.2f})"`; otherwise `"ok"`.
   (Coverage = share of camera-facing vertices that land inside the photo's silhouette.)

## Do — part B: UE textured material (`unreal/import_character.py`)
1. `plan_import`: `"material"` becomes `"textured"` when the mesh has `kind == "fused"` and
   `material.basecolor`; `"garment"` stays for other kinds with `material.basecolor` (T38); otherwise
   `"vertex_color"`. Only keys `basecolor`, `normal`, `roughness`, `metallic` become texture paths (skip `tint`;
   this also closes the T26 review note).
2. New `ensure_textured_material(entry) -> str` for `"textured"` entries:
   - Import the PNG: `AssetImportTask` with `filename = entry["textures"]["basecolor"]`,
     `destination_path = entry["destination"]`, `destination_name = f"T_{entry['asset_name']}_BaseColor"`,
     `automated`, `save`, `replace_existing` all `True`; `asset_tools.import_asset_tasks([task])`;
     texture path = first of `task.get_editor_property("imported_object_paths")`.
   - Material `M_{asset_name}` in the same folder: if it exists, `unreal.EditorAssetLibrary.delete_asset(path)`
     first (reruns stay clean). Create it with `asset_tools.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())`.
   - `sample = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, 0)`;
     `sample.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(texture_path))`;
     `mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)`.
   - Roughness constant 0.6 → `MP_ROUGHNESS` (as in `ensure_vertex_color_material`); `mel.recompile_material(mat)`;
     save; return the material path.
3. In `_import_fbx`, assign that material for `"textured"` (like the vertex-colour branch does).
   Leave `ensure_garment_material` alone (T38).

## Tests
- `tests/test_s06_garments.py`: extend the fake `run_blender` so `project_texture.py` copies `--in` to `--out`
  and prints `PROJECT_STATS {"scale_px_per_m": 1100.0, "photo_vertex_share": 0.3, "coverage": 0.9, "hidden_vertices": 0, "tex_px": 4096, "seconds": 1.0}`,
  and `render_previews.py` writes into whatever `--out-dir` it gets. New/updated cases:
  1. default config (`project_front`): status `ok`; cleanup `--out` ends with `character_vc.glb`; projection
     `--image` ends with `front_rgba.png`, `--tex-px` is `"4096"`; previews rendered twice (fused/ and
     fused/vertex_colors/); `data["texture"] == "project_front"`, `data["coverage"] == 0.9`.
  2. coverage 0.5 → `warn` with the exact message.
  3. `mvp_texture: vertex_colors` → no projection call; cleanup `--out` ends with `character_fused.glb`.
  4. `mvp_texture: "banana"` → `fail` with the exact message and the model is never called.
  5. projection prints no stats line → `fail` with the exact message.
  The existing real-Blender test: set `mvp_texture` to `vertex_colors` in its config copy (its fake model has
  no photo-shaped silhouette); `tests/test_project_texture.py` already covers the real projection.
- `tests/test_unreal_plan.py`: fused + basecolor → `"textured"` with an absolute basecolor path; a `tint` key
  is not in `textures`; a garment with basecolor → `"garment"`.

## Verify
1. `ruff check src tests unreal scripts` and `pytest -q` → paste the summary lines.
2. Re-run s06 to s09 on the three T25 jobs (TRELLIS runs again with the same seed, about 1–2 min each):
   ```bash
   for j in 20261010-104423-71096a 20261010-105049-4e1f93 20261010-110015-135a05; do
     avatar-forge rerun /workspace/jobs/$j --from s06_garments --to s09_export
     python -c "import json,sys; m=json.load(open(sys.argv[1]+'/manifest.json')); print(m['stages']['s06_garments']['status'], m['stages']['s06_garments']['data'])" /workspace/jobs/$j
   done
   ```
3. `python scripts/preview_sheet.py --compare /workspace/jobs/20261010-104423-71096a /workspace/jobs/20261010-105049-4e1f93 /workspace/jobs/20261010-110015-135a05`
   → tell the owner to download `jobs/_review/s06_previews.png` and send it to Opus. Do not judge quality.
4. Set T28 `done`, commit `T28: <summary>` and push. Tell the owner: "T28 done; please send
   jobs/_review/s06_previews.png to Opus. Next is T27."

## Escalate if
- `project_texture.py` fails on a real mesh, or coverage is below 0.7 on more than one sample (alignment
  needs Opus), or a UE error appears that the card's API calls do not explain.

## Log

- `source ~/.avatar_forge_env && ruff check src tests unreal scripts`:
  `/bin/bash: line 1: ruff: command not found` (exit 127).
- `source ~/.avatar_forge_env && pytest -q`:
  `/bin/bash: line 1: pytest: command not found` (exit 127).
- Runtime check: `which python` returned `/usr/bin/python` (expected
  `/opt/venv-af/bin/python`); `python -m pytest --version` returned
  `/usr/bin/python: No module named pytest`. `/opt/venv-af/bin/python` and
  `avatar-forge` are unavailable.
- `python -m py_compile src/avatar_forge/stages/s06_garments.py
  unreal/import_character.py tests/test_s06_garments.py tests/test_unreal_plan.py`:
  passed.
- `git diff --check`: passed.
- After the configured pod environment was restored:
  - `ruff check src tests unreal scripts` → `All checks passed!`
  - `pytest -q` → `152 passed, 5 warnings in 63.09s`
  - `pytest -q tests/test_s06_garments.py tests/test_unreal_plan.py` →
    `12 passed in 4.98s`
  - `avatar-forge rerun /workspace/jobs/20261010-104423-71096a --from s06_garments --to s09_export`
    → `ok`, coverage `0.915`; hidden vertices `76543`; project seconds `19.3`.
  - `avatar-forge rerun /workspace/jobs/20261010-105049-4e1f93 --from s06_garments --to s09_export`
    → `ok`, coverage `0.935`; hidden vertices `91080`; project seconds `18.4`.
  - `avatar-forge rerun /workspace/jobs/20261010-110015-135a05 --from s06_garments --to s09_export`
    → `ok`, coverage `0.881`; hidden vertices `91651`; project seconds `19.9`.
  - `python scripts/preview_sheet.py --compare /workspace/jobs/20261010-104423-71096a /workspace/jobs/20261010-105049-4e1f93 /workspace/jobs/20261010-110015-135a05`
    → `jobs/_review/s06_previews.png`

### Opus review (2026-10-16) — re-run needed (E-026), no code changes for the worker
The worker's glue and tests are correct. The black textures were Opus's bug: `cleanup_mesh.py` exported
flat-shaded faces, so every triangle had its own 3 vertices (a "triangle soup"). Smart UV Project then made
~148k one-triangle islands (almost the whole atlas black) and the visibility rays misfired (hidden 76–91k).
Fixed in `cleanup_mesh.py` (faces smooth → shared vertices) and `project_texture.py` (welds and smooths its
input itself); regression tests added and shown to fail on the old code.
**To finish T28 (worker):** `git pull`, set T28 `doing`, then re-run Verify steps 1–3 only (ruff, pytest, the
three re-runs, the `--compare` preview sheet). Expect `hidden_vertices` in the hundreds or low thousands, not
tens of thousands. Append the new output under a "Re-run after E-026" heading in this Log, set `done`, commit
`T28: re-run after E-026`, push, and ask the owner to send the new preview sheet to Opus.

