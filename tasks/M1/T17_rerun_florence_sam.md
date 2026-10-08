# T17 — Re-run the Florence-2 + SAM parsing trial after the box fix
milestone: M1 · effort: low · depends: T13
owner input: none

## Goal
Opus review of T13 found that `parsing_florence2_plus_sam.py` passed `(height, width)` to
Florence-2's `post_process_generation`, which expects `(width, height)`. On portrait images every
box was scaled wrongly, so the T13 florence2-plus-sam masks are invalid. The fix (plus
`MAX_NEW_TOKENS = 256`, which should stop the c_front stall) is already committed. Re-run the trial.

## Read first
- tasks/M1/T13_trials_parsing.md (Log only)

## Do
1. New terminal: `source ~/.avatar_forge_env && cd ~/avatar-forge && git pull && which python`
   (must be `/opt/venv-af/bin/python`).
2. Delete the old outputs: `rm -rf jobs/_model_trials/parsing/florence2-plus-sam`.
3. Re-run on all six BiRefNet cut-outs exactly as T13 did (same inputs, same command), with
   `timeout 2400s`. Then `python scripts/trials_report.py`.
4. Paste the summary (ok/failed per image, total time) into the Log, set T17 done, commit
   `T17: <summary>`, push.

## Must not
- Change the wrapper again. If results still look wrong or it stalls, record it and escalate.

## Verify
- `ruff check src tests` · `pytest -q`
- REPORT.md shows the new florence2-plus-sam result.

## Log
