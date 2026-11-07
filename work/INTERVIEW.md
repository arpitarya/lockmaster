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

*Updated 2026-11-07 (Claude Code, Opus 5.5 — W-10, W-15 built; W-09, W-13, W-14 closed).*
**Where things stand:** the tool works and lands in all five repositories:
milo and sheetpane had their first landings on 2026-11-07 (W-09 closed), and
fux's long-held W-11 handoff landed the same day. `src/lockmaster/` implements
SR-ARCHITECTURE decisions 1–20. Landing is continuous (W-11). **W-10:** a
landing stopped only by uncommitted edits in main's checkout **waits** and
lands by itself once they clear; `work/NOW.md` never makes a landing wait.
**W-15:** `install` creates any of the six work files a repository lacks,
`doctor` names a missing or stale one, and the kit's `work-files.py` Stop hook
tells a session once that it touched none of WORKLOG, INTERVIEW or OPEN-WORK.
L8, L9 and L10 are `built: yes`. 150 scratch-repo tests pass on Python 3.9.
Nothing is on PyPI until the decider finishes W-08.

## 2 · In flight, and the immediate next step

**Blocked on the decider** (`work/BLOCKED.json`): milo keeps its trackers in
`tv-movies/work/`; does L10 count those, or does milo get the six at its root?
milo keeps its adopted kit until then. **Next agent step** once ruled: install
the new kit into milo (and into codelaw, once no session is live there — one
was on 2026-11-07), land it with `lockmaster save`, close W-15. W-08 waits on
the decider too. `lm/W-09` and `lm/handoff-20261105-055911` are kept,
unmerged branches `doctor` names: the decider rules (SR-WORK-CLEANUP decision 3).

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
- **The Cowork bridge never commits** (SR-ARCHITECTURE decision 19): it cannot
  unlink, and it sees the Mac's repositories at another path, so a prune from
  it would cut off the Mac's worktrees. Its shell can write `.claude/` and
  `.git/` (its file tools cannot); git there runs with no optional locks.
  Edits from Cowork land through `lockmaster save` → a handoff.

## 4 · Lessons learned

- 2026-10-28: anything lockmaster writes that names a path names the machine
  that wrote it — the merge drivers were registered with the bridge's paths
  twice. `work/LESSONS.md` has it; decision 10 now heals it.
- 2026-10-28: an independent review of W-11 before it landed found eight
  faults the author's tests missed — the worst landed another session's
  change. For a change that runs in every session's hooks, review first.

- A dogfood landing on a copy of this repo went red on its first try because
  the test worklog entry named a work-item id that has no item file — the
  work-system check refused it. Landing through the repo's real checks finds
  what unit tests on scratch repos cannot.

- lockmaster exists because of lessons fux, sheetpane and codelaw each
  recorded: a commit swept another session's staged files; generated files
  conflicted; seven parallel builds filled the disk; a ruling sat on an
  unmerged branch for days. SR-ARCHITECTURE §2 Context names them.
