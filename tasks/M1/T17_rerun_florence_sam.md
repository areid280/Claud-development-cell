# T17 — Re-run the Florence-2 + SAM parsing trial after the box fix
milestone: M1 · effort: low · depends: T13
owner input: none

## Goal
Opus review of T13 found that `parsing_florence2_plus_sam.py` passed `(height, width)` to
Florence-2's `post_process_generation`, which expects `(width, height)`. On portrait images every
box was scaled wrongly, so the T13 florence2-plus-sam masks are invalid. The fix (plus
`MAX_NEW_TOKENS = 256`, which should stop the c_front stall) is already committed. Re-run the trial.

## Read first
- this card only (the commands are complete below)

## Do
1. New terminal: `source ~/.avatar_forge_env && cd ~/avatar-forge && git pull && which python`
   (must be `/opt/venv-af/bin/python`).
2. Delete the old outputs: `rm -rf jobs/_model_trials/parsing/florence2-plus-sam`.
3. Re-run with these exact commands (Opus, E-009; from the T13 run). The trial harness names
   outputs by file stem, so the BiRefNet cut-outs are copied to `<stem>.png` first:
   ```bash
   source ~/.avatar_forge_env && cd ~/avatar-forge
   IN=/tmp/af-t17-inputs; rm -rf "$IN"; mkdir -p "$IN"
   for d in jobs/_model_trials/bg_remove/birefnet/*/; do
     stem=$(basename "$d"); [ -f "$d/cutout.png" ] && cp "$d/cutout.png" "$IN/$stem.png"
   done
   ls "$IN"     # expect the 6 sample stems (a_front, a_back, b_front, c_front, bad_*)
   timeout 2400s python scripts/trial_model.py --role parsing --name florence2-plus-sam --images "$IN"/*.png
   python scripts/trials_report.py
   ```
   If `ls "$IN"` shows fewer than 6 files, use the rembg cut-out for the missing stem
   (`jobs/_model_trials/bg_remove/rembg/<stem>/cutout.png`) and note it in the Log.
4. Paste the summary (ok/failed per image, total time) into the Log, set T17 done, commit
   `T17: <summary>`, push.

## Must not
- Change the wrapper again. If results still look wrong or it stalls, record it and escalate.

## Verify
- `ruff check src tests` · `pytest -q`
- REPORT.md shows the new florence2-plus-sam result.

## Log

- Sourced `~/.avatar_forge_env`; `which python` was `/opt/venv-af/bin/python`. Removed the old `florence2-plus-sam` outputs and staged the six available BiRefNet cut-outs (`a_back`, `a_front`, `b_front`, `bad_cropped_feet`, `bad_crossed_arms`, `c_front`); no rembg fallback was needed.
- Ran the exact `timeout 2400s python scripts/trial_model.py --role parsing --name florence2-plus-sam --images /tmp/af-t17-inputs/*.png` command and regenerated the report. Per image: all six failed (`a_back`, `a_front`, `b_front`, `bad_cropped_feet`, `bad_crossed_arms`, `c_front`). Each failed loading `Florence2Processor` from the cached dynamic module with `AttributeError: ... processing_florence2 has no attribute 'Florence2Processor'`. Report: 0/6 successful; mean 6.377 s/image, max VRAM 0.000 GB (approximately 38.3 seconds total from the rounded mean); no PNG outputs.
- Escalated as E-010 without changing the wrapper. T17 remains blocked pending Opus resolution.
- After E-010 resolution (commit `5efe269`), removed old outputs and restaged all six BiRefNet inputs; no rembg fallback was needed. The exact trial command succeeded for five images: `a_back` 145.788s, `a_front` 136.071s, `b_front` 115.867s, `bad_cropped_feet` 122.709s, and `bad_crossed_arms` 120.322s. Each has `ok: true` and label/parts outputs.
- `c_front` then stalled with no trial record/output for over 10 minutes. At about 11m39s elapsed, `nvidia-smi` showed 0% GPU utilization and no listed process; stopped trial PIDs 10086 and 10085. `trials_report.py` did not run on this attempt. Escalated as E-011; T17 remains blocked.
- After E-011 resolution, accepted the repeated stall as a quality finding and did not rerun `c_front`. Regenerated `jobs/_model_trials/REPORT.md`; the report omits `florence2-plus-sam` because the interrupted run did not write its aggregate summary. Successful images remain recorded above: 5/6 (about 640.8 seconds summed; mean 128.2 seconds per successful image).
- c_front: failed — stall on stylised input, ~11 min, GPU idle (reproducible, T13 + T17).
- Validation: `ruff check src tests` -> `All checks passed!`; `pytest -q` -> `41 passed in 5.27s`.
