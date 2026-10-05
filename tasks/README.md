# Task cards

Every piece of work is a **task card**: a small, self-contained instruction
file a Sonnet worker can finish in one chat session.

## Card format

```
# T<id> — <title>
milestone: M<n> · effort: low|medium · depends: T.., G..
owner input: none | <what the human must provide first>

## Goal            one or two sentences
## Read first      the ONLY files to open (plus AGENTS.md)
## Do              numbered steps, exact paths and names
## Must not        things that are out of scope
## Verify          exact commands; expected result
## Done when       checklist
## Escalate if     card-specific triggers (in addition to AGENTS.md §4)
## Log             worker pastes real command output here
```

## Status values (in STATUS.md)

`todo` → `doing` → `done`, or `blocked` (see ESCALATIONS.md).
`waiting-owner` means the card needs something from the human (an image,
a screenshot, a UE5 test run) and the worker has asked for it.

## Who writes cards

- These cards were written at planning time.
- At each gate, Opus rewrites the **next** milestone's cards with what it learned.
- Opus creates fix cards (next free id, e.g. T28) when a gate finds problems.
- Workers never create or rewrite cards; they only fill in `## Log`.
