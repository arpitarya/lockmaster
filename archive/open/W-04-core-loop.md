---
type: Handoff
name: W-04
description: "Arpit, 2026-10-25: build step 2 of the lockmaster design — the core loop."
item: W-04
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Claude Code (Opus 5.5), closed — built"
ball: none
closed: 2026-10-25
---

# W-04 — the core loop: start, claim, submit, run, queue

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `start <item> --paths …`: branch `lm/<item>`, a worktree, the claim in the state directory | a change exists | ✅ |
| 2 | `claim add`, `submit`, `queue` | a change can be widened, queued and seen | ✅ |
| 3 | `run`: the landing of decision 8, under the land lock | changes reach `main`, one at a time | ✅ |
| 4 | Red handling: reason to the agent; inbox row when it stays red | nothing forced, nothing lost | ✅ |
| 5 | The forks W-02 ruled 2026-10-25: `submit` starts `run`; a red change is set aside, the next lands | auto-run and red behaviour as decided | ✅ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Opus: the landing is the heart of the tool and its failure modes lose work.

## Goal

An agent can claim, work, submit and see its change land on `main` — only its claimed paths, generated files rebuilt, checks passed — with its worktree gone afterwards.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · happy path | two changes from two worktrees land one after the other in a scratch repo; `main` holds two fast-forward commits with `Lockmaster-Change:` trailers | ✅ |
| 2 · claims | a file outside the claim is left behind and reported, never committed | ✅ |
| 3 · red | a conflicting change goes red with its reason; nothing on `main` or in its worktree is lost | ✅ |
| 4 · cleanup | a landed change's worktree and branch are removed as SR-WORK-CLEANUP decides | ✅ |

## Outcome

**Closed 2026-10-25 (Claude Code, Opus 5.5) — built.** `src/lockmaster/land.py`: `start`, `claim add`, `submit` (starts `run`), `run` under the land lock (`repo.py`), red set aside with its reason and a ready inbox row, `abandon`, `queue`. One design point the records forced: SR-LAW-3 decision 2 allows only `git branch -d`, so when the whole branch landed the landing commit records the branch tip as a second parent — `main` still moves by fast-forward, and `git log --first-parent` reads the landings alone. Tests: `tests/test_land.py` (every DoD row and both hazards), and a dogfood run on a copy of this repo with its own checks. The live answer is SR-ARCHITECTURE decisions 3–8, 11.

## Blockers

None — W-02 ruled 2026-10-25 (SR-ARCHITECTURE decisions 6 and 11).

## Record affected

SR-ARCHITECTURE decisions 3–8, 11 and 14.

## Hazards

- Two `run`s at once: the land lock must make the second wait or exit, never interleave.
- A crash mid-landing must leave `main` untouched and the change still queued.

## Reference

- [SR-ARCHITECTURE](../../records/0101_architecture.md) · [SR-WORK-CLEANUP](../../records/0062_WORK-cleanup.md)
