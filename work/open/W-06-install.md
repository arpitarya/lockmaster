---
type: Handoff
name: W-06
description: "Arpit, 2026-10-25: build step 4 of the lockmaster design — one kit, installed, not copied by hand."
item: W-06
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-06 — lockmaster install: the kit into any repository

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lockmaster install <repo>`: copy `kit/claude` → `.claude/`, `kit/github` → `.github/`, merge `settings.json` without losing the repo's own entries | one source for every repo's hooks | ⏳ |
| 2 | Record the installed kit version in the target (`.claude/lockmaster.lock` or similar) | pinned, upgradeable on purpose | ⏳ |
| 3 | Retire `scripts/bootstrap.py` here, and fux's `install-agent-hooks.py` | nothing hand-copied remains | ⏳ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Sonnet: file copying with a careful JSON merge.

## Goal

Any repository gets the work-system hooks, settings and skill by one command, at a known version.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · install | a fresh scratch repo gets `.claude/` and `.github/` and passes `check-work-system.py`'s hook rows | ⏳ |
| 2 · merge | a repo's own extra hooks in `settings.json` survive an install and a reinstall | ⏳ |
| 3 · pinned | the installed version is written down and `lockmaster doctor` reports a mismatch | ⏳ |

## Blockers

None.

## Record affected

SR-ARCHITECTURE decisions 14 and 15.

## Hazards

- `.claude/` and `.github/` refuse writes from the Cowork bridge: install runs on the Mac (Claude Code or a terminal).

## Reference

- [SR-ARCHITECTURE](../../records/0101_architecture.md) · [`scripts/bootstrap.py`](../../scripts/bootstrap.py)
