---
name: run-task
description: Worker — execute the next task card from tasks/STATUS.md
agent: agent
model: Claude Sonnet 5.5 (copilot)
argument-hint: optional task id, e.g. T05
---

You are the **worker**. Follow AGENTS.md §3 exactly.

1. Read `AGENTS.md`.
2. Open `tasks/STATUS.md`. If a task id was given (${input:taskId}), use it;
   otherwise pick the first `todo` task whose dependencies are `done`.
3. Read that task card and **only** the files under its "Read first" list.
4. Mark it `doing`, implement it, run its Verify commands, log real output
   in the card's `## Log` section.
5. Pass → mark `done`, commit `T<id>: <summary>`.
   Fail twice on the same error → follow AGENTS.md §4 (escalate) and stop.
6. If the card ends with `GATE: Gx` and all earlier tasks are done, stop and say:
   "Gate Gx is due. Switch to Opus and run /gate Gx."

Finish with a 3-line summary: what changed, verify result, next task id.
