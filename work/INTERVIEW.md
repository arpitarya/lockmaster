---
type: Handoff
description: "Cold-start state of play for a successor session: in-flight work, constraints, lessons."
---

# Model handoff — the agent-succession record

*The departing model answers for the record, so whatever succeeds it inherits
the judgment and not just the files.*

**Standing instruction to every future model reading this: you are now the
maintainer of this document. When the project's direction, decisions or state
change, update it in the same change. Leave it better.**

## How to use this file

A state-of-play doc, not an end-of-session report. Keep it current **during**
the session. Write it for a different model arriving with zero other context,
mid-task. The four sections below are maintained; anything after them is
history. **A stale INTERVIEW at handoff is as serious as a missing worklog
entry.**

---

## 1 · State of play

*Updated 2026-10-25 (Claude Code, Opus 5.5 — W-03 to W-07 built).*
**Where things stand:** the tool works. `src/lockmaster/` implements
SR-ARCHITECTURE decisions 1–16: claims, the queue, landing under the land
lock, red set aside, generated files rebuilt, three structural merge drivers,
`status`/`doctor`, `install`; the kit carries `claim-guard.py` and
`block-main.py`. 53 scratch-repo tests pass on Python 3.9. Committed
on `main` with the previous session's work.
**Not yet done here:** the kit is not installed in this repo (`.claude/` does
not exist), so `scripts/check-work-system.py` fails on the `.claude/hooks/*`
ownership rows until it is — the same check passes on a copy after an install.
The laws in force are L0–L7; L6 makes lockmaster **Python only, on PyPI only**.

## 2 · In flight, and the immediate next step

Nothing in flight. **Next:** the decider runs
`PYTHONPATH=src python3 -m lockmaster install .` (kit into `.claude/` and
`.github/`, merge drivers, commit guard) and commits that. From then on an
agent session here cannot commit to `main`: it uses `lockmaster start` /
`submit`. Then W-08 (the decider's PyPI placeholder) and W-09 — which waits,
by its own hazard, until each of fux, sheetpane and codelaw has an empty
`work/NOW.md` (fux and codelaw had live rows on 2026-10-25).

## 3 · Standing constraints

- The laws: L0 (records are the only source; links, never restatements), L1
  (retired records are archived), L2 (`work/MACHINE.md`'s budget section — 5 GB
  for the project, every GB past it approved first).
- Python ≥ 3.9, standard library only (SR-ARCHITECTURE decision 2): the
  decider's Mac runs `python3` 3.9.
- Edit `kit/`, never `.claude/` or `.github/` directly: `lockmaster install .`
  overwrites them and `lockmaster doctor` reports a hand edit (`CLAUDE.md` §Layout).
- Nothing in `src/` or `kit/claude/` may contain the forbidden git strings, not
  even in a comment: CI greps for them, and so does `tests/test_regen.py`.
- `main`'s first-parent chain is the landings; when a whole branch lands its
  tip is the landing's second parent, so `git branch -d` can prove it merged
  (SR-LAW-3 decision 2 allows nothing stronger).
- The Cowork bridge cannot write `.claude/` or `.github/`, and cannot unlink:
  installs and cleanups run on the Mac.

## 4 · Lessons learned

- A dogfood landing on a copy of this repo went red on its first try because
  the test worklog entry named a work-item id that has no item file — the
  work-system check refused it. Landing through the repo's real checks finds
  what unit tests on scratch repos cannot.

- lockmaster exists because of lessons fux, sheetpane and codelaw each
  recorded: a commit swept another session's staged files; generated files
  conflicted; seven parallel builds filled the disk; a ruling sat on an
  unmerged branch for days. SR-ARCHITECTURE §2 Context names them.
