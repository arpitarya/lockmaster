---
type: Handoff
name: W-07
description: "Arpit, 2026-10-25: build step 5 of the lockmaster design — status is computed, not written."
item: W-07
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: arpit
---

# W-07 — lockmaster status, and NOW.md as its generated view

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lockmaster status`: live sessions, open changes, worktrees, disk use against L2's budget | one command shows what is live | ⏳ |
| 2 | `work/NOW.md` regenerated from it; `now-ledger.py` writes through it | NOW.md cannot drift | ⏳ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Sonnet.

## Goal

What is being worked on right now is answered from git and lockmaster's state, never from a hand-edited file.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · status | shows every live change and worktree in a scratch repo with two sessions | ⏳ |
| 2 · NOW.md | equals `lockmaster status --now` after every landing and every session end | ⏳ |

## Blockers

W-04 (changes must exist to report).

## Record affected

SR-ARCHITECTURE decision 14; SR-WORK-NOW decisions 2–5.

## Hazards

- A Cowork session runs no hooks: its row must still be addable by hand until status can see it.

## Reference

- [SR-WORK-NOW](../../records/0061_WORK-now.md)
