---
type: Handoff
name: W-06
description: "Arpit, 2026-10-25: build step 4 of the lockmaster design — one kit, installed, not copied by hand."
item: W-06
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Claude Code (Opus 5.5), closed — built"
ball: none
closed: 2026-10-25
---

# W-06 — lockmaster install: the kit into any repository

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lockmaster install <repo>`: copy `kit/claude` → `.claude/`, `kit/github` → `.github/`, merge `settings.json` without losing the repo's own entries | one source for every repo's hooks | ✅ |
| 2 | Record the installed kit version in the target (`.claude/lockmaster.lock` or similar) | pinned, upgradeable on purpose | ✅ |
| 3 | Retire `scripts/bootstrap.py` here, and fux's `install-agent-hooks.py` | nothing hand-copied remains | ✅ here; fux's is W-09's |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Sonnet: file copying with a careful JSON merge.

## Goal

Any repository gets the work-system hooks, settings and skill by one command, at a known version.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · install | a fresh scratch repo gets `.claude/` and `.github/` and passes `check-work-system.py`'s hook rows | ✅ |
| 2 · merge | a repo's own extra hooks in `settings.json` survive an install and a reinstall | ✅ |
| 3 · pinned | the installed version is written down and `lockmaster doctor` reports a mismatch | ✅ |

## Outcome

**Closed 2026-10-25 (Claude Code, Opus 5.5) — built.** `src/lockmaster/install.py` (`lockmaster install <repo> [--backup]`: kit copied, `settings.json` merged, `.claude/lockmaster.lock` written, merge drivers and commit guard installed) and `doctor.py`. `scripts/bootstrap.py` moved to `archive/scripts/`; `records/RULE-SINCE` got the first commit's sha. Retiring fux's `install-agent-hooks.py` is fux's change and belongs to W-09. Tests: `tests/test_install.py`; on a copy of this repo, an install turns `scripts/check-work-system.py` green. Open: the wheel does not carry `kit/` yet (B-005). The live answer is SR-ARCHITECTURE decisions 14 and 15.

## Blockers

None.

## Record affected

SR-ARCHITECTURE decisions 14 and 15.

## Hazards

- `.claude/` and `.github/` refuse writes from the Cowork bridge: install runs on the Mac (Claude Code or a terminal).

## Reference

- [SR-ARCHITECTURE](../../records/0101_architecture.md) · [`scripts/bootstrap.py`](../../scripts/bootstrap.py)
