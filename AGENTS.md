# AGENTS.md — rules for every AI coding agent on this repo

Read this file fully at the start of every session. It is short on purpose.

## 1. What we are building

`avatar-forge`: a command-line pipeline (later a small UI) that takes 1–4 full-body
images of an **adult** character and produces a rigged, game-ready character for
Unreal Engine 5:

- a MetaHuman-compatible body (face, body shape, skin, hair colour)
- each clothing item as a **separate mesh** with its own PBR textures
- editable body parameters (height, bust, waist, hips, etc.) with a
  "normalise proportions" step
- export as FBX (+ textures) that UE5 imports cleanly

Full brief: `docs/00_PROJECT_BRIEF.md`. Architecture: `docs/01_ARCHITECTURE.md`.

## 2. Who does what (model tiers)

| Tier | Model | Use for |
|------|-------|---------|
| **Worker** | Claude Sonnet (low/medium effort) | Executing a single task card in `tasks/`. Boilerplate, tests, glue code, UI, scripts, docs updates. |
| **Gatekeeper** | Claude Opus (high effort) | Running gates in `gates/`, architecture changes, licence decisions, debugging escalations, judging output quality. |

The human owner switches models in the chat model picker. **Workers never
"pretend" to be the gatekeeper.** If a gate is due, stop and say so.

## 3. The worker loop (follow exactly)

1. Open `tasks/STATUS.md`. Pick the **first** task with status `todo` whose
   dependencies are all `done`. Do not skip ahead.
2. Read **only**: that task card, the files it lists under "Read first", and
   this file. Do not scan the whole repo (it wastes budget).
3. Set the task's status to `doing` in `tasks/STATUS.md`.
4. Implement exactly what the card asks. Nothing extra. No refactors of
   other files unless the card says so.
5. Run the card's "Verify" commands. Paste the real output into the task
   card under `## Log` (trim long output to the last 40 lines).
6. If verify passes: set status `done`, commit with message
   `T<id>: <short summary>`.
7. If the card says `GATE: Gx` at the bottom and all tasks before the gate
   are done → **STOP** and tell the human:
   `Gate Gx is due. Switch to Opus and run /gate Gx.`

## 4. Escalation rules (stop and hand to Opus)

Stop work, write `tasks/ESCALATIONS.md` entry (template inside), set the task
status to `blocked`, and tell the human to switch to Opus **if any of these
happen**:

- The same error persists after **2** fix attempts.
- A fix would require changing anything in `schemas/` or `docs/01_ARCHITECTURE.md`.
- A model, dataset or asset must be chosen or replaced (licence question).
- GPU / CUDA / driver / build-from-source problems you cannot fix by
  following `docs/04_ENVIRONMENT.md`.
- Visual quality must be judged (meshes, textures, proportions).
- Anything touches secrets, tokens, SSH keys or paid services.
  (Running `git pull`/`git push` with the owner's already-saved credential is allowed;
  never read, print, type, create or edit a token or credential file. D-004.)
- The task card is ambiguous or contradicts another file.

Escalating early is cheaper than looping. Never guess at licences.

## 5. Coding rules

- Python 3.11. Package lives in `src/avatar_forge/`. Type hints everywhere.
- Every pipeline stage is a module in `src/avatar_forge/stages/` with one
  public function `run(ctx: StageContext) -> StageResult`. Do not change this
  signature (see `src/avatar_forge/core/stage.py`).
- Implementing a stage? Also read `docs/06_STAGE_CONTRACTS.md` (what `ctx` and
  `StageResult` provide). It answers the usual "how do I read/write/warn" questions.
- Stages communicate **only** through files in the job folder and the
  `manifest.json` described by `schemas/character_manifest.schema.json`.
  Never pass data between stages in memory globals.
- Heavy third-party models are wrapped in `src/avatar_forge/models/<name>.py`
  and loaded lazily. Weights go in `$AF_WEIGHTS_DIR` (default `/workspace/weights`),
  **never** in git.
- Every external model must be listed in `config/models.yaml` with its
  licence and a `licence_ok` field. Only Opus at a gate may set
  `licence_ok: true`.
- Config values come from `config/pipeline.yaml`. No magic numbers in code.
- On the pod, every terminal must load the environment first: `source ~/.avatar_forge_env`.
  `which python` must print `/opt/venv-af/bin/python`; if not, fix the terminal before any `pip`.
- Log with `logging` via `avatar_forge.core.log.get_logger`. No `print` in library code.
- Tests in `tests/` use `pytest`. Tests that need a GPU are marked
  `@pytest.mark.gpu` and are skipped automatically without one.
- Keep each commit small (ideally under ~300 changed lines).

## 6. Content and consent rules (non-negotiable)

- Input subjects must be **adults**: original characters, or real people who
  have consented. The input validator must keep the consent/adult
  confirmation flag (see `docs/00_PROJECT_BRIEF.md` §5).
- Do not add features designed to remove clothing from images or likenesses
  of real, identifiable people. Body editing operates on the 3D character.
- Do not commit test images of real people to the repo. Use `samples/` which is git-ignored.

## 7. Budget discipline

- One task card per chat session. Start a new chat for the next card.
- Do not paste whole large files into chat; reference them by path.
- Do not run long GPU jobs to "see what happens". Each card says what to run.
- If you notice you are re-reading the same files repeatedly, stop and escalate.

## 8. Where things are

```
AGENTS.md                  this file
docs/                      brief, architecture, environment, decisions
tasks/STATUS.md            the task board — single source of truth
tasks/M*/T*.md             task cards
tasks/ESCALATIONS.md       escalation log
gates/G*.md                gate checklists (Opus only)
gates/reports/             gate reports written by Opus
schemas/                   JSON schemas (data contracts) — Opus-owned
config/                    pipeline.yaml, models.yaml
src/avatar_forge/          the package
scripts/                   setup + smoke tests
tests/                     pytest
unreal/                    UE5-side notes and Python import scripts
assets/garment_library/    garment templates (not in git; see README there)
samples/                   test inputs (git-ignored)
```
