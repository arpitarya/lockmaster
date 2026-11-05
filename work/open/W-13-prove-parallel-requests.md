---
type: Handoff
name: W-13
description: "Arpit, 2026-11-05: L8 — lockmaster handles parallel requests. Nothing tests it with real concurrent processes; prove it, and fix what the proof finds."
item: W-13
filed: 2026-11-05
filed_by: "Cowork (Opus 5.5), on Arpit's ruling of L8"
updated: 2026-11-05
updated_by: "Cowork (Opus 5.5): built — steps 1–4; lands with the next Claude Code session"
ball: agent
---

# W-13 — prove L8: parallel requests, with real concurrent processes

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | A scratch-repo test that starts several processes at once — `start` + `submit` from different worktrees, `save` and `pickup` from `main`'s checkout, `sync` — and waits for the queue to drain | L8's veto condition becomes a command | ✅ `tests/test_parallel.py`, six processes per case |
| 2 | It asserts [SR-LAW-8](../../records/0010_LAW-8-parallel-requests.md) decisions 2–6: every change landed (or red for a real reason), no torn file in the state directory, no caller told to retry, nothing landed under another change | proof, not prose | ✅ |
| 3 | Fix what step 2 finds — e.g. what happens after the third `main`-moved retry (decision 5), two `start`s of one item at once | the law holds | ✅ found and fixed: saves in one second took one name; handoffs written at once overwrote each other; two end-of-turn landings of one session could commit in one worktree at once; a second `start` of one item now says so plainly; a pickup re-reads before it lets go. After three `main`-moved retries a landing still goes red — only something other than lockmaster can move `main` mid-landing |
| 4 | Point SR-LAW-8's veto check at the test; register's `built` for SR-LAW-8 → `yes` | the law is checked | ✅ |

**Arpit, 2026-11-05:** *"lock master should handle parallel requests."*

**Model:** Sonnet.

## Definition of done

- A multi-process test in `tests/` covers decisions 2–6 and passes on Python 3.9.
- SR-LAW-8's *How to check it* names it.

## Record affected

[SR-LAW-8](../../records/0010_LAW-8-parallel-requests.md); [SR-ARCHITECTURE](../../records/0101_architecture.md) decisions 6–8 if a fix changes them.
