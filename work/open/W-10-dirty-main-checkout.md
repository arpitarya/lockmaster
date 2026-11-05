---
type: Handoff
name: W-10
description: "Arpit, 2026-10-27: uncommitted edits in main's checkout turned three codelaw landings red with an empty reason; lockmaster should name the blocking files, wait instead of going red, and warn before it happens."
item: W-10
filed: 2026-10-27
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-28
updated_by: "Cowork (Opus 5.5): step 1 in part by W-11; codelaw ids marked as codelaw's"
ball: agent
---

# W-10 — a dirty `main` checkout: name it, wait it out, warn before it happens

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | When `merge --ff-only` in `main`'s checkout is refused, find the cause: the checkout's uncommitted paths (`git status --porcelain`) that the landing commit touches. The reason names them: *"main's checkout at <path> has uncommitted edits to work/OPEN-WORK.md, … that this landing would overwrite"* — never an empty line | the decider sees why, at a glance | ◐ [W-11](../../archive/open/W-11-land-every-turn-and-cowork-handoff.md), SR-ARCHITECTURE decision 8a: edits identical to the landing are staged and the fast-forward goes; differing ones are named, never an empty line. Left: the step-2 behaviour for the differing case |
| 2 | That cause is not red: the change is **waiting** (a new status, or `queued` with a `waiting_on` reason). The landing commit is kept; `lockmaster run` retries waiting changes on each pass and on `submit`, and fast-forwards as soon as the overlap is gone. Every other cause stays red (decision 11) | no resubmit by hand for a cause that clears itself | ⏳ |
| 3 | `lockmaster status` and `doctor` list uncommitted edits in `main`'s checkout that overlap a queued, waiting or open change's claim, with the change's id | the clash is visible before the landing | ⏳ |
| 4 | A kit hook (beside `claim-guard.py`) warns a session that edits, in `main`'s checkout, a path an open change claims: *"<item> claims this file; edit it in its worktree or through lockmaster"* | the cause is stopped at the source | ⏳ |
| 5 | Tests in scratch repos: an edit in the checkout overlapping the landing → waiting with the paths named → the edit is committed elsewhere or reverted → the next `run` lands it; an edit not overlapping → lands at once; the checkout's edit is never touched (L3) | proof | ⏳ |

**Arpit, 2026-10-27:** *"Yes, let's file it as a lock master work item."* — on the proposal after the codelaw incident below.

**Model:** Sonnet.

## What happened (codelaw, 2026-10-27)

A Cowork session with no lockmaster access edited codelaw's `work/OPEN-WORK.md`, `README.md`, `CHANGELOG.md` and others directly in `main`'s checkout and left them uncommitted. A Claude Code session committed the same edits on its `lm/` branch in codelaw and submitted. `merge --ff-only` in the checkout refused, so **codelaw W-36** — and **codelaw W-85** and **codelaw W-91**, which also touch `work/OPEN-WORK.md` — went **red**. `lockmaster queue` showed only *"main's checkout at /Users/arpitarya/my_programs/codelaw refused the fast-forward:"* with **nothing after the colon**: git's message was lost (`(e or o)` empty). The work queue looked frozen for about 40 minutes. **codelaw W-36** and **codelaw W-85** landed by 08:47 IST once the checkout was clean; **codelaw W-91** needed a resubmit.

## Seen again (lockmaster, 2026-11-05) — `save` blocks itself on `work/NOW.md`

`lockmaster save` from main's checkout copied 53 edited paths into its worktree; the kit's `now-ledger.py` then wrote the new worktree's row into the checkout's `work/NOW.md`. The landing held the copy without that row, so decision 8a found `work/NOW.md` differing and the fast-forward was refused (red, reason empty after the colon again). Copying the checkout's `NOW.md` into the worktree and resubmitting landed it (`9c747a7`). Fix with this item: `save` should leave `work/NOW.md` out of its copy (it is live state, SR-WORK-NOW), or 8a should accept a ledger-only difference.

## Definition of done

- The reason for a refused fast-forward names the overlapping paths, or says git gave none, never an empty line.
- A change blocked only by the checkout lands with no resubmit once the checkout is clean.
- `status` and `doctor` show the overlap; the kit hook warns on it.
- Scratch-repo tests for steps 1–5; no path in the checkout is ever changed by lockmaster (L3).

## Record affected

[SR-ARCHITECTURE](../../records/0101_architecture.md) decision 11 (the checkout cause becomes *waiting*, not red) and decision 8 (the fast-forward's failure reason); [SR-WORK-CLEANUP](../../records/0062_WORK-cleanup.md) if `doctor`'s report changes; the glossary (*waiting*).

## Hazards

- [L3](../../records/0005_LAW-3-never-lose-work.md): never stash, reset, clean or overwrite the checkout's edits to make a landing go — waiting is the only remedy lockmaster applies.
- A waiting change holds its landing commit while `main` moves; on retry it must be redone on the new `main` (decision 8's three tries), not fast-forwarded from a stale base.
- A session without lockmaster (Cowork linked to the Mac) cannot see the hook; step 3 is its only signal — say so in the kit's agent text.

## The row to add to `work/OPEN-WORK.md` when this lands

This file was written into `main`'s checkout as a new, untracked file only — the checkout already held another session's uncommitted queue edits, so the row was **not** added there (the very clash this item is about). Add it under `### build`, and bump `## Open items` and `### build` by one, in the landing change:

```
🟢 **W-10** `agent` A dirty `main` checkout: a refused fast-forward names the overlapping files, the change waits and lands once they clear (not red), `status`/`doctor` and a kit hook warn first. Filed by Arpit (Cowork). [detail](open/W-10-dirty-main-checkout.md)
```
