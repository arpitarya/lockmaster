---
type: Handoff
name: W-09
description: "Arpit, 2026-10-25: once installable, lockmaster replaces the hand-copied work-system hooks in fux, sheetpane and codelaw."
item: W-09
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Claude, cloud linked to the Mac, Opus 5.5)"
ball: agent
---

# W-09 — adopt lockmaster in fux, sheetpane, codelaw and milo

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lockmaster install` into each repo | one kit, four repos | sheetpane ✅ · milo ✅ · fux ⏳ · codelaw ⏳ — both had live sessions on 2026-10-25 (hazard below) |
| 2 | A `lockmaster.toml` per repo: its checks, generated files, merge drivers | each repo's own rules | sheetpane ✅ · milo ✅ · fux ⏳ · codelaw ⏳ |
| 3 | Retire the copied hooks and `install-agent-hooks.py` | nothing drifts | sheetpane ✅ (two hand copies replaced by the kit) · fux ⏳ · codelaw ⏳ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Sonnet, one repo at a time — never three in parallel (L2).

## Goal

fux, sheetpane and codelaw run the same kit at a pinned version, and each declares its own generated files.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · fux | installed; `.fux/index/**`, `llms*.txt`, `CHANGELOG.md` regenerated on landing | ⏳ |
| 2 · sheetpane | installed; its generated files declared | ✅ 2026-10-25 — `llms.txt`, `llms-full.txt` |
| 3 · codelaw | installed; its generated files declared | ⏳ |
| 4 · milo | installed (Arpit, 2026-10-25: *"Lockmaster is ready to be consumed by Fux, Sheetpane, Codelaw, and Milo"*); no work system there, so the NOW hooks stay silent | ✅ 2026-10-25 |

## Blockers

None — W-06 closed 2026-10-25: `lockmaster install` exists.

## Record affected

Each repo's own records that own `.claude/hooks/*` — amended there, not here.

## Found while adopting (2026-10-25)

- The kit carried lockmaster's own `ci.yml`; `install --backup` would have moved each repo's CI aside. Removed from the kit — a repository's CI is its own (SR-ARCHITECTURE decisions 15–16 amended).
- `now-ledger.py` crashed and `require-progress.sh` nagged in a repo with no `work/NOW.md` (milo). Both are silent there now; tested.
- `install` run from the Linux VM writes the VM's python and path into `.git/config`'s merge drivers; they were re-pointed at the Mac's (`/Library/Developer/CommandLineTools/usr/bin/python3 ~/my_programs/lockmaster/src/lockmaster/merge.py`).

## Hazards

- Each repo has its own concurrent sessions: install when its `work/NOW.md` is empty.

## Reference

- [W-06](../../archive/open/W-06-install.md) (closed) · [SR-ARCHITECTURE](../../records/0101_architecture.md) decisions 14–15
