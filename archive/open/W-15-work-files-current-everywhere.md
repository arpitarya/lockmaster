---
type: Handoff
name: W-15
description: "Arpit, 2026-11-05: L10 — the six work files are always up to date in every repository lockmaster is installed in. Today only judgment enforces it; install does not create them and no check names a missing or stale one."
item: W-15
filed: 2026-11-05
filed_by: "Cowork (Opus 5.5), on Arpit's ruling of L10"
updated: 2026-11-08
updated_by: "Claude Code (Opus 5.5): installed in codelaw — closed"
ball: agent
---

# W-15 — enforce L10: the work files current in every repository

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lockmaster install` creates any of the six files a repository lacks, from a short template in `kit/` (never overwrites one) | [SR-LAW-10](../../records/0012_LAW-10-work-files-current.md) decision 6 | ✅ `kit/work/`, `install.work_files` |
| 2 | `lockmaster doctor` names a missing work file, and a repository whose landings since the last `WORKLOG.md` change exceed a set number | the drift is visible | ✅ `doctor.work_problems`; stale = more than 10 commits on `main` since `WORKLOG.md` last changed |
| 3 | A kit Stop hook beside `require-progress.sh`: a session that changed tracked files outside `work/` but touched none of `WORKLOG.md`, `INTERVIEW.md`, `OPEN-WORK.md` is told once, before it stops | decision 4, at the source | ✅ `kit/claude/hooks/work-files.py` (`edit` notes each write, `stop` tells once) |
| 4 | Scratch-repo tests for steps 1–3; install it into the five repositories | proof, and the law reaches every user | ✅ `tests/test_work_files.py` (13 tests); landed in lockmaster (`599fade`), sheetpane (`1e04930`, docket `6c971b6`), fux (`4c135a0`, docket `7e7cfe7`), codelaw (`794da39`, 2026-11-08 — its kit-file rows added to its own SR-WORK-SESSION and register); milo left alone by the decider's ruling |

**Arpit, 2026-11-05:** *"open work, backlog, interview, machine, lessons, worklog should always be upto date who so ever uses lockmaster."*

**Model:** Sonnet.

## Installed in codelaw (2026-11-08)

The decider asked for it with a session live in codelaw; none of that session's
four open changes claimed a kit file, so the install went ahead. It first
refused: codelaw had hand-edited its installed `docket` skill to add its own
queue group (`reporting and benchmarks`). The kit's skill now names no group
(`a86244f`), codelaw's edit was moved aside by `--backup` and removed only once
its bytes matched codelaw's `HEAD`. codelaw's `work-system` check then wanted
`work-files.py` in its ownership table: added to its SR-WORK-SESSION `owns:`
and register.

## Ruled (2026-11-07)

**Arpit, 2026-11-07, later the same day (Claude Code):** *"Leave milo alone"* —
milo keeps its trackers in `tv-movies/work/` and L10 counts them; the new kit is
not installed there for now. This supersedes the reading below: asked again
because a `git mv` would make tv-movies' own trackers milo's repo-wide ones
(milo's `CLAUDE.md`: *"Modules stay self-contained"*, with `apps/ios` arriving
as a second module), rewrite about sixty relative links, and collide with an
uncommitted edit in `tv-movies/docs/archive/open-work-rules.md`. `lockmaster
doctor` in milo still names its root work files missing — accepted.

### Superseded: the first reading of the ruling

**Arpit, 2026-11-07:** *"Root work/"* — milo gets the six work files at its root `work/`, like every other repository. Next agent step: in milo, `git mv` `tv-movies/work/{OPEN-WORK,INTERVIEW,WORKLOG,IMPLEMENTATION}.md` to `work/` (history kept, nothing lost — L3), then `lockmaster install .` adds the two missing files; land with `lockmaster save`.

### The question as it was put

milo keeps its trackers in `tv-movies/work/` (`OPEN-WORK`, `INTERVIEW`,
`WORKLOG`, `IMPLEMENTATION`) and has no root `work/`. A fresh `install` there
would write a second set of six at the root. Asked in the inbox: does L10 count
`tv-movies/work/`, or does milo get the six at its root? Until then milo keeps
the kit it adopted (`4a99fa8`). codelaw gets the new kit once the Claude Code
session live there on 2026-11-07 has ended (the hazard: install when its
`work/NOW.md` is empty).

## Definition of done

- A fresh `lockmaster install` leaves all six files present.
- `doctor` and the Stop hook catch a missing or untouched work file; tests prove it.
- No check claims to judge LESSONS, MACHINE or BACKLOG content — that stays judgment (SR-LAW-10 §Consequences).

## Record affected

[SR-LAW-10](../../records/0012_LAW-10-work-files-current.md); [SR-ARCHITECTURE](../../records/0101_architecture.md) decision 15 (the kit).
