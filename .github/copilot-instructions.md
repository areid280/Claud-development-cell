# Copilot instructions

All rules for this repository are in [AGENTS.md](../AGENTS.md). Read it at the
start of every session and follow it exactly.

Short version:

- Work on **one** task card at a time, the first `todo` in `tasks/STATUS.md`.
- Read only the files the card lists. Do not scan the whole repo.
- Run the card's Verify commands and log real output in the card.
- Stop and escalate to Opus on the triggers in AGENTS.md §4
  (2 failed fixes, schema change, licence choice, GPU build problems,
  visual-quality judgement, secrets, ambiguity).
- When a gate is due, stop and tell the human: "Gate Gx is due. Switch to Opus and run /gate Gx."
- Never commit model weights, secrets or images of real people.

Reusable prompts (type `/` in Copilot Chat):

- `/run-task` — worker executes the next task card (Sonnet)
- `/gate` — gatekeeper runs a quality gate (Opus)
- `/escalate` — gatekeeper resolves a blocked task (Opus)
