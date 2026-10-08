# T14 — Trials: body measurements
milestone: M1 · effort: medium · depends: T12
owner input: for each sample image, your best guess of the character's height, bust, waist and hips in cm (a rough guess is fine; used as reference)

## Goal
Compare ways to get body measurements (cm) from an image, including our own licence-free fallback.

## Read first
- config/models.yaml → role `body_measure`
- schemas/body_params.schema.json (measurement keys)
- config/pipeline.yaml → `stages.s04_body_fit`
- the pose wrapper you judged best in T12

## Do
1. **In-house fallback** `src/avatar_forge/body/keypoint_ratio.py`:
   ```python
   def measure(keypoints: dict, alpha: np.ndarray, height_cm: float, cfg: dict) -> dict[str, float]
   ```
   - Pixel height = (lower of: lowest heel/ankle keypoint y, lowest alpha pixel y)
     minus (top-most alpha pixel y). Big hair or a hat inflates this; subtract
     `stages.s04_body_fit.hair_allowance_frac` (new key, default 0.02) of the height
     when a `hat` or large `hair` mask sits above the head.
   - Scale `cm_per_px = height_cm / pixel_height`.
   - Widths: silhouette width (alpha row span, ignoring arms by clipping to the
     torso between hip/shoulder x-range ±15%) at: bust line (25% of the way from
     shoulders to hips), underbust (35%), waist (narrowest row between 40–70%),
     hips (widest row between hip keypoints and 15% below).
   - Circumference ≈ ellipse perimeter with width `w` and depth `w * depth_ratio`;
     depth ratios from new config keys `stages.s04_body_fit.depth_ratio`
     (`bust: 0.75, underbust: 0.70, waist: 0.70, hips: 0.72`). Use Ramanujan's approximation.
   - shoulder_width = distance between shoulder keypoints × 1.15 × cm_per_px;
     inseam = mean hip→ankle length × 0.92 × cm_per_px.
   - Unit tests with a synthetic alpha mask (rectangles) and hand-made keypoints
     in `tests/test_keypoint_ratio.py`; check scale and monotonicity (wider mask → larger circumference).
2. **Mesh-based candidates moved to T18** (Opus, E-008). Do not implement `mesh_measure.py`,
   mesh wrappers or `render_previews.py` here.
3. Trial adapter `trial_adapters_body.py` with one trial, `keypoint-ratio`: pose from the
   **rtmlib-rtmw** wrapper (T12, 6/6), alpha from the BiRefNet cut-out
   (`jobs/_model_trials/bg_remove/birefnet/<stem>/cutout.png`), `height_cm` from
   `samples/reference.yaml` (fall back to `stages.s04_body_fit.default_height_cm`). Write
   `measurements.json` with all schema keys in cm.
4. Add the owner's reference measurements to `samples/reference.yaml` and make
   `scripts/trials_report.py` show error % per measurement against it when present.

## Must not
- Use any external body model (SAM 3D Body, SMPL/SMPL-X). That is T18.

## Verify
- `pytest -q` green (new keypoint_ratio tests) · REPORT.md includes body_measure with error %.

## Log
