# T44 — MetaHuman parameter mapping
milestone: M4 · effort: medium · depends: T41
owner input: UE version; screenshots of MetaHuman Creator body panel; test runs of the UE script

> **Opus investigates and rewrites this card at G3** (what the installed UE
> version allows from Python is the main unknown — see docs/03 §3).

## Goal
Get from `body_params.json` to a matching MetaHuman with as few manual steps as possible.

## Do (outline)
1. `src/avatar_forge/body/metahuman_map.py`: measurements → MetaHuman body
   parameters (whatever the installed version exposes), plus colours → skin tone,
   hair melanin/redness, eye colour approximations.
2. UE script: apply automatically where the API allows; otherwise print a
   clear table of values to set by hand.
3. Owner verifies with screenshots; record the mapping accuracy in Log.

## Log
