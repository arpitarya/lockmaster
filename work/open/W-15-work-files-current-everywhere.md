---
type: Handoff
name: W-15
description: "Arpit, 2026-11-05: L10 — the six work files are always up to date in every repository lockmaster is installed in. Today only judgment enforces it; install does not create them and no check names a missing or stale one."
item: W-15
filed: 2026-11-05
filed_by: "Cowork (Opus 5.5), on Arpit's ruling of L10"
updated: 2026-11-07
updated_by: "Claude Code (Opus 5.5): steps 1–3 built; step 4's tests built, its installs next"
ball: agent
---

# W-15 — enforce L10: the work files current in every repository

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lockmaster install` creates any of the six files a repository lacks, from a short template in `kit/` (never overwrites one) | [SR-LAW-10](../../records/0012_LAW-10-work-files-current.md) decision 6 | ✅ `kit/work/`, `install.work_files` |
| 2 | `lockmaster doctor` names a missing work file, and a repository whose landings since the last `WORKLOG.md` change exceed a set number | the drift is visible | ✅ `doctor.work_problems`; stale = more than 10 commits on `main` since `WORKLOG.md` last changed |
| 3 | A kit Stop hook beside `require-progress.sh`: a session that changed tracked files outside `work/` but touched none of `WORKLOG.md`, `INTERVIEW.md`, `OPEN-WORK.md` is told once, before it stops | decision 4, at the source | ✅ `kit/claude/hooks/work-files.py` (`edit` notes each write, `stop` tells once) |
| 4 | Scratch-repo tests for steps 1–3; install it into the five repositories | proof, and the law reaches every user | ◐ `tests/test_work_files.py` (13 tests) ✅; installed in lockmaster ✅; the other four ⏳ |

**Arpit, 2026-11-05:** *"open work, backlog, interview, machine, lessons, worklog should always be upto date who so ever uses lockmaster."*

**Model:** Sonnet.

## Definition of done

- A fresh `lockmaster install` leaves all six files present.
- `doctor` and the Stop hook catch a missing or untouched work file; tests prove it.
- No check claims to judge LESSONS, MACHINE or BACKLOG content — that stays judgment (SR-LAW-10 §Consequences).

## Record affected

[SR-LAW-10](../../records/0012_LAW-10-work-files-current.md); [SR-ARCHITECTURE](../../records/0101_architecture.md) decision 15 (the kit).
