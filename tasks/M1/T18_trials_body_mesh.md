# T18 — Trials: mesh-based body measurement (SAM 3D Body; SMPL-X optional)
milestone: M1 · effort: medium · depends: T14
owner input: SMPL-X only if the owner has registered at smpl-x.is.tue.mpg.de and says so

## Goal
Measure the same keys as T14 from a body mesh, so G1 can compare mesh models with the in-house
keypoint method. Opus split this out of T14 (E-008) and defined the slicing rules below.

## Read first
- tasks/M1/T14_trials_body_measure.md (Do + Log)
- config/models.yaml → `body_measure`; src/avatar_forge/models/base.py; docs/05_DECISIONS.md D-007, D-008

## Licence / access rules (Opus)
- Trials do not need `licence_ok` (E-003); licences are judged at G1. Under D-008 non-commercial is fine.
- **smpler-x:** skip unless the owner states they registered and accepted the SMPL-X licence. Record
  "skipped: needs owner SMPL-X registration".
- **sam-3d-body:** follow its README. If weights are gated on Hugging Face and the download returns
  401/403, stop that candidate and record "needs owner HF access request". Never handle tokens.
  If it needs torch > 2.4.1 (install fails on the constraint), record "needs newer torch (D-007)".
  The 30-minute rule applies.

## Do
1. `src/avatar_forge/body/mesh_measure.py`:
   ```python
   def measure_mesh(vertices: np.ndarray, faces: np.ndarray, height_cm: float, cfg: dict) -> dict[str, float]
   ```
   - Up axis = the axis with the largest vertex extent. Floor = min along it; stature = extent.
     Scale all vertices so stature == `height_cm` (work in cm).
   - Slice heights are **fractions of stature from the floor** in new config
     `stages.s04_body_fit.mesh_slice` (add to pipeline.yaml):
     `bust: 0.72`, `underbust: 0.68`, `waist_range: [0.58, 0.66]`, `hips_range: [0.46, 0.54]`, `range_steps: 9`.
   - At each height use `trimesh.intersections.mesh_plane` / `trimesh.Trimesh.section` and take the
     closed loops in the plane. **Torso loop** = the loop whose polygon contains the torso centre
     (mean of vertices within ±1 cm of the plane, projected); if none contains it, the
     largest-area loop. Perimeter of that loop = circumference.
   - waist = **minimum** torso perimeter over `range_steps` heights in `waist_range`;
     hips = **maximum** over `hips_range`.
   - shoulder_width / inseam: if the wrapper also returns 3D joints, compute as T14 does from
     shoulder and hip→ankle joints; otherwise omit those keys.
   - Tests `tests/test_mesh_measure.py` with `trimesh.creation.cylinder` (radius r, height h):
     every circumference ≈ 2πr after scaling (±2%), and a cylinder with two thin "arm" cylinders
     beside it still returns the central loop.
2. Wrapper `src/avatar_forge/models/body_measure_sam3d_body.py` → `predict(image_rgba) -> (vertices, faces, joints|None)`.
3. Extend `trial_adapters_body.py` with a trial per mesh candidate: `measurements.json`, `mesh.glb`,
   and `front.png`/`back.png` via `run_blender` + the existing `src/avatar_forge/blender/render_previews.py`
   (args `--in <glb> --out-dir <dir> [--size 768]`; already written and tested by Opus, E-012).
4. Run trials, append installs to `docs/INSTALL_LOG.md`, rerun `scripts/trials_report.py`.

## Must not
- Change `selected`/`licence_ok`. Upgrade torch. Commit weights, meshes or renders.

## Verify
- `ruff check src tests` · `pytest -q` (mesh_measure tests run on CPU)
- REPORT.md body_measure lists keypoint-ratio and each mesh candidate (ok, failed or skipped with reason).

## Log
