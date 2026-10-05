# 02 — Model tiers, gates and budget

## 1. Why two tiers

Most of this project is routine code that a cheaper model writes well when the
instructions are exact. A few moments decide whether the project succeeds:
choosing models, approving licences, judging visual quality and fixing hard
bugs. Those go to the stronger, more expensive model.

| Work | Model | Effort |
|------|-------|--------|
| Task cards (`/run-task`) | Claude Sonnet 5.5 | low; medium for cards marked `effort: medium` |
| Gates (`/gate Gx`) | Claude Opus 5.5 | high |
| Escalations (`/escalate`) | Claude Opus 5.5 | high |
| Tiny edits (typos, renames) | cheapest included model | — |

Check that the `model:` line in each `.github/prompts/*.prompt.md` file matches
the exact name shown in your Copilot model picker. Change it there if not.

## 2. When the worker must hand over to Opus

See AGENTS.md §4. In short: 2 failed fixes, schema or architecture change,
licence choice, GPU/build trouble, visual-quality judgement, secrets,
or an unclear task card.

## 3. Gates

| Gate | After | Opus decides |
|------|-------|--------------|
| G0 | M0 | Environment is sound and reproducible |
| G1 | M1 | Which models we use; licences approved; M2 cards refined |
| G2 | M2 | MVP works end-to-end; quality worth continuing; M3 cards refined |
| G3 | M3 | Garment separation quality; M4 cards refined |
| G4 | M4 | Body editing and refit quality; M5 cards refined |
| G5 | M5 | Release readiness |

Each gate ends with PASS, PASS WITH FIXES or FAIL. FAIL means stop and talk
to the human; don't keep spending.

At G1–G4 Opus also **rewrites the next milestone's task cards** using what was
learned. The later cards in this repo are deliberately a little less detailed
for that reason.

## 4. Budget

Copilot charges Opus requests at a much higher rate than Sonnet requests
(the multiplier depends on your plan and changes over time; check your
GitHub billing page). Plan on roughly:

- ~35–45 worker sessions (one per task card, plus fix cards)
- 6 gates + a handful of escalations on Opus

Rules that keep the bill down:

- One task card per chat. Start a fresh chat for each card.
- Never use Opus to write routine code.
- Escalate after 2 failed attempts; looping on Sonnet costs more than one Opus call.
- Check usage in GitHub billing after each gate. If more than ~25% of the
  budget is gone before G2, ask Opus at G2 to cut scope.

The **rented GPU is a separate cost** (RunPod, about $0.34/hr for an
RTX 4090 on Community Cloud at the time of writing). Stop the pod whenever
you're not running it. The storage volume costs a little even when stopped.
