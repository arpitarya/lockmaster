---
type: Handoff
name: W-09
description: "Arpit, 2026-10-25: once installable, lockmaster replaces the hand-copied work-system hooks in fux, sheetpane and codelaw."
item: W-09
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-09 — adopt lockmaster in fux, sheetpane and codelaw

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lockmaster install` into each repo | one kit, three repos | ⏳ |
| 2 | A `lockmaster.toml` per repo: its checks, generated files, merge drivers | each repo's own rules | ⏳ |
| 3 | Retire the copied hooks and `install-agent-hooks.py` | nothing drifts | ⏳ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Sonnet, one repo at a time — never three in parallel (L2).

## Goal

fux, sheetpane and codelaw run the same kit at a pinned version, and each declares its own generated files.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · fux | installed; `.fux/index/**`, `llms*.txt`, `CHANGELOG.md` regenerated on landing | ⏳ |
| 2 · sheetpane | installed; its generated files declared | ⏳ |
| 3 · codelaw | installed; its generated files declared | ⏳ |

## Blockers

W-06.

## Record affected

Each repo's own records that own `.claude/hooks/*` — amended there, not here.

## Hazards

- Each repo has its own concurrent sessions: install when its `work/NOW.md` is empty.

## Reference

- [W-06](W-06-install.md)
