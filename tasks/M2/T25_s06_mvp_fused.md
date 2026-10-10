# T25 — Stage s06_garments, MVP fused mesh
milestone: M2 · effort: medium · depends: T24

> **G1 (Opus, 2026-10-09, D-014):** image_to_3d = **trellis** (`models/i23d_trellis.py`, class `Trellis`),
> fallback triposr. nvdiffrast may be loaded (owner confirmed scope, D-014 addendum).
> **E-024 (Opus, 2026-10-10):** the Blender clean-up script, its tests, the config keys and the TRELLIS
> install script are **already written and tested by Opus**. This card is now: the stage glue, its unit
> tests, and the real run.

## Goal
A clean, correctly scaled single mesh of the whole character, as proof the 3D path works.

## Read first
- docs/06_STAGE_CONTRACTS.md (AGENTS.md §5 requires it for every stage)
- src/avatar_forge/stages/s06_garments.py (stub + contract)
- config/pipeline.yaml (`stages.s06_garments`: `mode` and the `mvp_*` keys; already added, do not edit)
- src/avatar_forge/models/registry.py (`load_selected`) and src/avatar_forge/models/base.py (`vram_peak_gb`, `reset_vram_peak`)
- src/avatar_forge/blender_runner.py (`run_blender`)
- src/avatar_forge/blender/cleanup_mesh.py (done; read its docstring and arguments only)
- tests/test_s04_body_fit.py (pattern for a hand-built `StageContext`)
- tests/test_cleanup_mesh.py (pattern for a `@pytest.mark.blender` test)

## Already done by Opus (do not change)
- `src/avatar_forge/blender/cleanup_mesh.py`: join, merge by distance, drop small loose parts, normals,
  decimate, scale to height, feet on z = 0, centred, export GLB with **linear** vertex colours
  (`--color-space srgb` fixes TRELLIS's display colours). Prints one line `CLEANUP_STATS {json}` with keys
  `triangles_in`, `triangles`, `parts_removed`, `scale`, `color_attributes`. Never rotates (E-018).
- `render_previews.py` now shows vertex colours (Workbench VERTEX) with the Standard view transform.
- `tests/test_cleanup_mesh.py` (passes with Blender 4.2).
- Config keys under `stages.s06_garments`: `mvp_max_triangles`, `mvp_merge_distance_m`,
  `mvp_min_part_fraction`, `mvp_color_space`, `mvp_seed`, `mvp_preview_px`.
- `scripts/install_trellis.sh`, run by `setup_pod.sh`; it must print `TRELLIS ready: ...`.

## Do
Implement `run(ctx)` in `src/avatar_forge/stages/s06_garments.py` exactly as follows.
1. `cfg = ctx.stage_config()`. If `cfg["mode"] == "separate"` return `StageResult.not_implemented("T30")`.
   Any other mode except `"mvp_fused"`: return
   `StageResult(status="fail", messages=[f"Unknown s06_garments mode '{mode}'"])`.
2. Inputs (missing files raise; do not catch):
   - `body = json.loads(ctx.previous_output("s05_body_params", "body_params.json").read_text(encoding="utf-8"))`;
     `height_m = body["measurements"]["height"] / 100.0`
   - `rgba_path = ctx.previous_output("s02_prepare", "front_rgba.png")`; open with PIL and `.convert("RGBA")`.
3. `fused = ctx.stage_dir / "fused"`; `fused.mkdir(parents=True, exist_ok=True)`.
4. Model (module-level imports so tests can monkeypatch `s06_garments.load_selected`):
   ```python
   reset_vram_peak()
   with load_selected("image_to_3d") as model:
       raw = model.predict(rgba, out_dir=fused, seed=int(cfg["mvp_seed"]), output_name="raw.glb")
       vram = vram_peak_gb()
   ```
   Log the model name and VRAM with `ctx.logger.info(...)`. Model name for `data`: `model.name`
   (read it inside the `with`).
5. Clean-up (module-level `from avatar_forge.blender_runner import run_blender`, monkeypatchable):
   ```python
   out = fused / "character_fused.glb"
   result = run_blender(
       BLENDER_DIR / "cleanup_mesh.py",
       ["--in", str(raw), "--out", str(out), "--height-m", f"{height_m:.4f}",
        "--max-tris", str(cfg["mvp_max_triangles"]), "--merge-dist", str(cfg["mvp_merge_distance_m"]),
        "--min-part-frac", str(cfg["mvp_min_part_fraction"]), "--color-space", str(cfg["mvp_color_space"])],
       ctx.config,
       log_path=ctx.job_dir / "logs" / "s06_garments_cleanup.blender.log",
   )
   ```
   where `BLENDER_DIR = Path(__file__).resolve().parents[1] / "blender"`. Parse the stats from the
   **last** stdout line starting with `"CLEANUP_STATS "` (`json.loads(line.split(" ", 1)[1])`). If there
   is none, return `fail` with message `"cleanup_mesh.py printed no CLEANUP_STATS line"`.
6. Previews: `run_blender(BLENDER_DIR / "render_previews.py", ["--in", str(out), "--out-dir", str(fused),
   "--size", str(cfg["mvp_preview_px"])], ctx.config, log_path=ctx.job_dir / "logs" / "s06_garments_previews.blender.log")`
   writes `fused/front.png` and `fused/back.png`.
7. `mesh = trimesh.load(out, force="mesh")`, then `mesh.merge_vertices(merge_tex=True, merge_norm=True)`
   (Blender's GLB splits vertices at hard edges, which makes even a closed cube look open to trimesh).
8. Return `StageResult(status="ok", outputs=[...], data={...})`:
   - `outputs` (relative, posix): `s06_garments/fused/raw.glb`, `.../character_fused.glb`, `.../front.png`, `.../back.png`
   - `data = {"model": name, "triangles": len(mesh.faces), "triangles_raw": stats["triangles_in"],
     "parts_removed": stats["parts_removed"], "watertight": bool(mesh.is_watertight),
     "height_m": round(height_m, 4), "vram_peak_gb": round(vram, 2)}`
   - Not watertight is normal for the MVP: still `ok`, no warning.
   - Do **not** write `garment.json` in this mode (the runner would put it in `manifest["garments"]`; T26 reads
     the fused GLB directly).
9. Update the stub docstring's "Reads/Writes" lines if they differ from the above. Nothing else in other files.

## Tests (`tests/test_s06_garments.py`)
Hand-build `StageContext` as in `tests/test_s04_body_fit.py`, with `config=load_pipeline_config()` and
`job_dir=tmp_path`; write `s05_body_params/body_params.json` (height 168) and a small
`s02_prepare/front_rgba.png`.
1. `mode` set to `separate` (copy the config dict and change it) → `status == "skipped"`.
2. `mode` set to `"banana"` → `fail` with the exact message.
3. **Fakes, no GPU, no Blender:** monkeypatch `s06_garments.load_selected` with a fake context-manager
   model (`name = "fake"`) whose `predict` writes `trimesh.creation.box().export(out_dir / output_name)`
   and records its `seed`; monkeypatch `s06_garments.run_blender` with a fake that records its args, copies
   `--in` to `--out` and returns `subprocess.CompletedProcess(args=[], returncode=0, stdout='CLEANUP_STATS {"triangles_in": 12, "triangles": 12, "parts_removed": 0, "scale": 1.68, "color_attributes": []}\n', stderr="")`
   for the cleanup call, and writes `front.png`/`back.png` for the previews call. Assert: status `ok`;
   the four outputs; `--height-m` is `"1.6800"`; `--max-tris` is `"150000"`; seed 0;
   `data["triangles"] == 12`, `data["model"] == "fake"`, `data["watertight"] is True` (a box is watertight).
4. Same fakes but the cleanup stdout has no stats line → `fail` with the exact message.
5. `@pytest.mark.blender`: fake model only (real Blender), a 2-colour box GLB like
   `tests/test_cleanup_mesh.py`; assert `character_fused.glb` is 1.68 m tall (trimesh bounds, Y-up), `data["watertight"] is True`
   (needs step 7's merge) and both previews exist.

## Verify
1. Fresh pod: `bash scripts/setup_pod.sh` → paste the `TRELLIS ready: ...` line. (If it prints the TRELLIS
   WARNING instead, stop and escalate with the output.)
2. `ruff check src tests` and `pytest -q` (Blender tests run on the pod) → paste the summary lines.
3. Real runs with the reference heights (each prints its job folder):
   ```bash
   avatar-forge run samples/a_front.png --confirm-adult-consent --to s06_garments --set height=168
   avatar-forge run samples/b_front.png --confirm-adult-consent --to s06_garments --set height=158
   avatar-forge run samples/c_front.png --confirm-adult-consent --to s06_garments --set height=188
   ```
   For each job paste: `python -c "import json,sys; m=json.load(open(sys.argv[1]+'/manifest.json')); print(m['stages']['s06_garments'])" <job>`
4. Describe the previews honestly per sample (holes? spikes? missing limbs? colours right?). Do **not** judge
   pass/fail: list the six preview paths for the owner to send to Opus (visual quality is Opus's call, AGENTS.md §4).

## Escalate if
- `TRELLIS ready` is not printed, CUDA out of memory, or any Blender script fails.
- The model output is consistently unusable (Opus decides whether to switch to triposr).

## Log

- `bash scripts/install_trellis.sh` -> `TRELLIS ready: 2.4.1+cu124 kaolin 0.17.0`.
- `ruff check src tests` -> `All checks passed!`
- `pytest -q` -> `134 passed, 3 warnings in 41.18s`.
- Real run `samples/a_front.png --set height=168` -> job `/workspace/jobs/20261010-104423-71096a`; s06 status `ok`, 148499 triangles (194436 raw), 5 parts removed, not watertight, height 1.68 m, peak VRAM 10.36 GB.
- Real run `samples/b_front.png --set height=158` -> job `/workspace/jobs/20261010-105049-4e1f93`; s06 status `ok`, 148498 triangles (240708 raw), 16 parts removed, not watertight, height 1.58 m, peak VRAM 10.43 GB.
- Real run `samples/c_front.png --set height=188` -> job `/workspace/jobs/20261010-110015-135a05`; s06 status `ok`, 148499 triangles (399148 raw), 9 parts removed, not watertight, height 1.88 m, peak VRAM 10.73 GB.
- Warp logged `Insufficient CUDA driver version: minimum required 13.0, installed driver 12.8` on each TRELLIS run; all three stages completed successfully.
- Preview images are listed for Opus visual review; visual quality has not been assessed here:
  - `/workspace/jobs/20261010-104423-71096a/s06_garments/fused/front.png`
  - `/workspace/jobs/20261010-104423-71096a/s06_garments/fused/back.png`
  - `/workspace/jobs/20261010-105049-4e1f93/s06_garments/fused/front.png`
  - `/workspace/jobs/20261010-105049-4e1f93/s06_garments/fused/back.png`
  - `/workspace/jobs/20261010-110015-135a05/s06_garments/fused/front.png`
  - `/workspace/jobs/20261010-110015-135a05/s06_garments/fused/back.png`
