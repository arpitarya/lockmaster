---
type: Log
description: "Dated lessons — what this project learned the hard way, newest first. A log, not a record: the date is part of the lesson."
---

# LESSONS — what this build learned the hard way

Newest first. A lesson whose remedy is a *rule* belongs in a record and is
named here only as the failure that produced it. A lesson whose remedy is
*judgment* lives here. ⚠ Nothing here is normative.

---

## 2026-11-07 — installing the kit from a change's worktree points the merge drivers at that worktree

Dogfooding means `lockmaster install .` after a kit edit, and the edit is made in
a change's worktree. The install registered the merge drivers in the shared
`.git/config` with the worktree's `src/lockmaster/merge.py`, a path that goes
away when the change lands. Every `run` re-points a driver whose path is missing
(the 2026-10-28 gate), so it heals, but a plain `git merge` in between would
use a dead driver. Remedy: judgment — after installing from a worktree, run
`lockmaster drivers` from main's checkout.

## 2026-11-05 — a one-line ruling drafted into a law grew a mechanism nobody ruled

The first draft of L9 required Cowork's handoffs to land "on their own" and
filed a background job to do it. The decider's ruling had said only "without
manual intervention", and when asked he chose the opposite: no background job,
the next Claude Code session lands them. A law drafted from one line states
what the ruling says; any mechanism it would need is a question for the decider
before it is written in, not after. Remedy: judgment.

## 2026-10-28 — a path written on one surface is wrong on the other

Installing from the Cowork bridge wrote the bridge's `python3` and `merge.py`
paths into five repositories' `.git/config` — the second time (W-09 recorded the
first, 2026-10-25, fixed by hand). Anything lockmaster writes that names a
path — a merge driver, a worktree, a `home` — names the machine that wrote it.
The bridge and the Mac see the same files at different paths, so a fix by hand
on one surface does not stop the next write from the other. Remedy, by the
two-strikes rule: a gate in code (SR-ARCHITECTURE decision 10), not a note.
