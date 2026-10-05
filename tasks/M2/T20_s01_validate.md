# T20 — Stage s01_validate
milestone: M2 · effort: low · depends: G1
owner input: `samples/bad_cropped_feet.png` and `samples/bad_crossed_arms.png` exist

> Opus refines this card at G1 (selected pose model name, any threshold changes).

## Goal
Reject unusable inputs with a clear reason; warn on weak ones.

## Read first
- src/avatar_forge/stages/s01_validate.py (contract)
- config/pipeline.yaml → `stages.s01_validate`
- docs/00_PROJECT_BRIEF.md §4
- the selected pose wrapper (`selected: true` under `pose` in config/models.yaml)

## Do
1. Split the logic so it is testable without a GPU:
   - `src/avatar_forge/stages/validate_rules.py`:
     ```python
     def evaluate(persons: list[dict], image_size: tuple[int, int], cfg: dict) -> tuple[str, list[str]]
     ```
     returns (`"ok"|"warn"|"fail"`, messages). Rules, in this order:
     | Rule | Result | Message |
     |------|--------|---------|
     | long side < `min_long_side_px` | fail | "Image is too small (WxH). Use at least N px on the long side." |
     | persons with score ≥ `keypoint_min_score` = 0 | fail | "No person found." |
     | count > `max_people` | fail | "More than one person found. Use one person per image." |
     | any `required_keypoints` below threshold | fail | "Not visible: <names>. Show the full body, head to toe." |
     | person bbox bottom within 1% of image bottom | fail | "Feet may be cut off at the bottom edge." |
     | person bbox top within 1% of image top | fail | "Head may be cut off at the top edge." |
     | bbox height / image height < `min_person_height_frac` | fail | "Person is too small in the frame." |
     | `warn_crossed_arms` and both wrists between the shoulders (x) and between shoulder and hip (y) | warn | "Arms look crossed; the torso and hands will be guessed." |
     | `warn_wrists_inside_torso` and one wrist inside the torso box | warn | "An arm covers the torso; that area will be guessed." |
   - Don't stop at the first failure: collect **all** fail messages, then all warn messages.
2. `run(ctx)`: for each view image from `s00_ingest`, load the selected pose
   model once (`with Wrapper(entry) as m:`), call `evaluate`, write
   `report.json` (`{view: {status, messages}}`) and `<view>_keypoints.json`.
   Overall status = worst across views.
3. `tests/test_validate_rules.py`: synthetic persons for every rule above
   (one test per row) plus one fully valid person → "ok".
4. GPU test `tests/test_s01_gpu.py` (`@pytest.mark.gpu`): run on
   `samples/bad_cropped_feet.png` → fail with "Feet"; skip if the sample is missing.

## Verify
- `pytest -q` · `avatar-forge run samples/a_front.png --confirm-adult-consent --to s01_validate`
  shows `ok` · `bad_cropped_feet` shows the feet message.

## Log
