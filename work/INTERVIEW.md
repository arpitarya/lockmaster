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

*Updated 2026-10-25 (Cowork, setup).*
**Where things stand:** the repository holds the work system — copied from
codelaw as it stood on 2026-10-25 — and the design of record, SR-ARCHITECTURE.
**No tool code yet:** `src/lockmaster/` is a stub that names its commands.
The laws in force are L0, L1 and L2; L3–L7 are proposed (W-01).

## 2 · In flight, and the immediate next step

Nothing in flight. **Next:** the decider runs `python3 scripts/bootstrap.py`
(installs `kit/` into `.claude/` and `.github/`, writes `records/RULE-SINCE`,
installs the commit guard), commits, and rules the inbox — W-01, W-02, W-08.
Agent-closable now: **W-03** and **W-06**.

## 3 · Standing constraints

- The laws: L0 (records are the only source; links, never restatements), L1
  (retired records are archived), L2 (`work/MACHINE.md`'s budget section — 5 GB
  for the project, every GB past it approved first).
- Python ≥ 3.9, standard library only (SR-ARCHITECTURE decision 2): the
  decider's Mac runs `python3` 3.9.
- Edit `kit/`, never `.claude/` or `.github/` directly: bootstrap overwrites
  them (`CLAUDE.md` §Layout).
- The Cowork bridge cannot write `.claude/` or `.github/`, and cannot unlink:
  installs and cleanups run on the Mac.

## 4 · Lessons learned

- lockmaster exists because of lessons fux, sheetpane and codelaw each
  recorded: a commit swept another session's staged files; generated files
  conflicted; seven parallel builds filled the disk; a ruling sat on an
  unmerged branch for days. SR-ARCHITECTURE §2 Context names them.
