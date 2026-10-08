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
