# avatar-forge

Turn 1–4 full-body images of an adult character into a rigged, game-ready
Unreal Engine 5 character, with every clothing item as a separate mesh,
editable body measurements, a "normalise proportions" step, and PBR textures.

**Status:** scaffold. Core plumbing, data contracts, task cards and quality
gates are in place; the pipeline stages are stubs to be filled in task by task.

## How this project is built

The code is written by AI coding agents in GitHub Copilot, in two tiers:

- **Worker (Claude Sonnet):** executes one small task card at a time from `tasks/`.
- **Gatekeeper (Claude Opus):** runs quality gates, picks models, approves
  licences, fixes escalations, and rewrites the next milestone's cards.

Start here:

1. `AGENTS.md` — the rules every agent follows.
2. `docs/00_PROJECT_BRIEF.md` — what we're building and the quality bar.
3. `docs/02_MODEL_TIERS_AND_BUDGET.md` — when to use which model, budget rules.
4. `tasks/STATUS.md` — the task board.

## Quick start (owner)

1. Follow `docs/04_ENVIRONMENT.md` (Windows PC + RunPod GPU + VS Code Remote-SSH). About 45 minutes.
2. On the pod: `bash scripts/setup_pod.sh`, then open a new terminal and run `bash scripts/doctor.sh`.
3. In Copilot Chat (Agent mode), choose Claude Sonnet and type `/run-task`.
4. When the agent says a gate is due, switch to Claude Opus and type `/gate G0` (etc.).
5. If the agent reports an escalation, switch to Opus and type `/escalate`.
6. Start a **new chat for each task card**, and **stop the pod** when you finish for the day.

## The day-to-day loop

```
Sonnet: /run-task  ->  card done, committed  ->  new chat  ->  /run-task ...
                    \-> stuck twice?  ->  Opus: /escalate  ->  back to Sonnet
                    \-> gate due?     ->  Opus: /gate Gx   ->  back to Sonnet
```

## Using the pipeline (once implemented)

```bash
avatar-forge run samples/a_front.png --back samples/a_back.png --confirm-adult-consent
avatar-forge rerun jobs/<job_id> --from s05_body_params --set height=172 --set bust=+10%
avatar-forge validate-manifest jobs/<job_id>
avatar-forge doctor
```

Results land in `jobs/<job_id>/s09_export/<job_id>/`. Import them into UE5 with
`unreal/import_character.py` (see `docs/03_UE5_INTEGRATION.md`).

## Content rules

Adults only. Inputs must be original characters or people who have consented.
The tool must not be used to strip clothing from images of real, identifiable
people. See `docs/00_PROJECT_BRIEF.md` §5.

## Repository map

See `AGENTS.md` §8.
