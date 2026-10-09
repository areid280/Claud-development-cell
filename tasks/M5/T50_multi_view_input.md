# T50 — Multi-view input
milestone: M5 · effort: medium · depends: G4
owner input: back (and ideally side) views of at least two sample characters

> **Opus note (T20 review, 2026-10-09):** `s01_validate` requires `nose` for every view, so back views would fail
> "Not visible: nose". Make `required_keypoints` per view (e.g. `required_keypoints_back` without face points)
> in `stages.s01_validate` and use it for `back` views.

> Planning-time draft. **Opus rewrites this card at G4.**

## Goal
Use back/left/right views when given, with checks that they show the same character.

## Do (outline)
1. CLI already accepts `--back --left --right`; make every stage from s01–s04 loop over views.
2. Consistency check in s01: same clothing colours per part (ΔE threshold) and
   similar height ratios; warn if views look like different characters.
3. Camera estimate per view (front 0°, right 90°, back 180°, left 270°) refined from keypoints.
4. Body fit uses side view depth when available (replace `depth_ratio` guesses).

## Log
