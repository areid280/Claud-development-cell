# T40 — Normalise proportions
milestone: M4 · effort: low · depends: G3

> Planning-time draft. **Opus rewrites this card at G3.**

## Goal
Pull unusual measurements back into the plausible adult ranges in config,
keeping the character recognisable.

## Read first
- config/pipeline.yaml → `stages.s05_body_params` (`normalise`, `strength`, `ranges_cm`, `ratios`)
- schemas/body_params.schema.json (`normalise` block)
- src/avatar_forge/body/overrides.py

## Do (outline)
1. `src/avatar_forge/body/normalise.py` (pure):
   `normalise(body, cfg) -> (body, changes)`.
   - Clamp each measurement toward its range by `strength`
     (`new = old + strength × (clamped − old)`).
   - Then ratios: adjust waist (not hips) to satisfy `waist_to_hips`;
     adjust underbust for `bust_minus_underbust_cm`; adjust inseam for
     `inseam_to_height`.
   - Record every change `{from, to, reason}` in `body["normalise"]`.
2. Order in s05: overrides first, then normalise (so user overrides beyond the
   range are allowed only when `--set normalise=false` or manifest
   `overrides.normalise == false`).
3. Tests: in-range body unchanged; out-of-range clamped; strength 0.5 halfway;
   each ratio rule; disabled flag.

## Log
