# T27 — End-to-end MVP run and evidence pack
milestone: M2 · effort: low · depends: T26
owner input: UE5 screenshots (front and back) of at least one imported character

## Goal
Collect everything Opus needs to make the G2 go/no-go decision.

## Read first
- gates/G2.md (so you know what evidence is needed)

## Do
1. Run `avatar-forge run <sample> --confirm-adult-consent` for every `samples/*_front.png`
   and both `bad_*` samples.
2. Write `scripts/summarise_jobs.py` → `gates/reports/G2_evidence.md` with a table:
   job, sample, each stage status, total seconds, height/bust/waist/hips, triangles,
   preview paths, and the s01 messages for the bad samples.
3. Ask the owner for UE5 screenshots; save them (if they're of original characters)
   as `docs/screenshots/G2_<sample>_<front|back>.png` and link them in the evidence file.
4. Mark T27 done and tell the human: "Gate G2 is due. Switch to Opus and run /gate G2."

## Verify
- `gates/reports/G2_evidence.md` exists and links every preview.

GATE: G2

## Log
