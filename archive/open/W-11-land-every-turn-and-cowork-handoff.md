---
type: Handoff
name: W-11
description: "Arpit, 2026-10-28: finished work in a worktree never reached main, and Cowork kept raising commit problems it could not fix. Land at the end of every turn; Cowork commits when it can, otherwise hands off to Claude Code."
item: W-11
filed: 2026-10-28
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-28
updated_by: "Cowork (Opus 5.5), closed — built"
ball: none
closed: 2026-10-28
---

# W-11 — land at the end of every turn; Cowork's edits landed by whichever surface can commit

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lockmaster sync` and the kit's `auto-land.py`: at each `Stop` a session's open changes land and stay open, the worktree following `main`; held (not red) when a check or conflict stops it; `claude --worktree` worktrees adopted; `SessionEnd` lands and cleans up | work reaches `main` turn by turn, conflicts stay small | ✅ |
| 2 | `lockmaster save` / `can-commit` / `pickup`: Cowork lands its edits where the surface can commit, else writes a handoff that the next Claude Code session lands | Cowork never has to ask the decider about commits | ✅ |
| 3 | Decision 8a: identical edits in `main`'s checkout no longer stop a fast-forward; differing ones are named | the codelaw W-36/W-113 reds do not recur for identical edits | ✅ |
| 4 | the `landing` skill for Cowork and Claude Code; `block-main.py` names `save` | agents on both surfaces know the one command | ✅ |
| 5 | installed into lockmaster, codelaw, fux, milo and sheetpane | the same behaviour in every repository | ✅ |
| 6 | Found reviewing the queue the same day: the end-of-turn landing runs in the background (fux's took 599 s — W-12), what it did is said at the next `Stop`; merge drivers registered from the bridge named the bridge's paths, a second time — `install` there registers none, `run` re-points them, `doctor` names them | no turn waits; structural merges work on the Mac | ✅ |

**Arpit, 2026-10-28:** *"Whenever we are working on work tree and the task is done, it doesn't merge the changes to main. That's what it should do. As soon as the changes are done, it should keep merging it to main so that there aren't too many conflicts later on. … If co-work can commit it, then it should go ahead and commit it. If co-work cannot commit it, then probably Claude Code should go ahead and commit it. Make the necessary changes and have it updated in all the repositories."*

**Model:** Cowork (Opus 5.5) — built from Cowork, which cannot commit; landed by the next Claude Code session through its own handoff.

## What was wrong

- A change landed only on `lockmaster submit`. Sessions that stopped without it left work on `lm/*` branches (codelaw on 2026-10-28: W-105, W-109-ruling, W-62 open, none submitted).
- The Cowork bridge cannot remove files, so `git commit` fails there; and it sees the Mac's repository at another path, so a `git worktree prune` from it would cut off every Mac worktree. Cowork's edits sat uncommitted in `main`'s checkout, turned landings red (codelaw W-113, 2026-10-28) and came back to the decider as questions.

## Definition of done

- A change with claimed work lands at the end of the turn and stays open; a failed check holds it, tells its agent once, and lands it the turn after the fix.
- `lockmaster save` lands checkout edits where the surface can commit, hands them off (exit 0) where it cannot; `pickup` lands, drops or holds each handoff.
- Identical checkout edits pass the fast-forward; differing ones are named; the checkout is never changed otherwise (L3).
- Tests: `tests/test_autoland.py`; the whole suite on Python 3.9, 3.11 and 3.13.

## Record affected

[SR-ARCHITECTURE](../../records/0101_architecture.md) decisions 8a, 11, 13, 14, 19 and 20; the glossary (*held*, *handoff*, *adopted*).
