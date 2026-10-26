---
type: Handoff
name: W-09
description: "Arpit, 2026-10-25: once installable, lockmaster replaces the hand-copied work-system hooks in fux, sheetpane and codelaw."
item: W-09
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-26
updated_by: "Arpit (Claude, cloud linked to the Mac, Opus 5.5)"
ball: agent
---

# W-09 — adopt lockmaster in fux, sheetpane, codelaw and milo

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lockmaster install` into each repo | one kit, four repos | ✅ sheetpane, milo 2026-10-25 · codelaw, fux 2026-10-26 (Arpit: *"implement in codelaw and fux"*; fux with a live session, by his word) |
| 2 | A `lockmaster.toml` per repo: its checks, generated files, merge drivers | each repo's own rules | ✅ all four |
| 3 | Retire the copied hooks and `install-agent-hooks.py` | nothing drifts | ✅ every hand copy replaced; fux's hook tests moved here as `tests/test_kit_hooks.py` (fux has no `install-agent-hooks.py` left to retire) |
| 4 | The first real landing in each repo, on the Mac | proof, and fux's per-landing index cost measured | ⏳ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Sonnet, one repo at a time — never three in parallel (L2).

## Goal

fux, sheetpane and codelaw run the same kit at a pinned version, and each declares its own generated files.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · fux | installed; `.fux/index`, `llms*.txt` rebuilt on landing (Arpit, 2026-10-26: *"Rebuild on landing"*); `CHANGELOG.md` is hand-written, so it is not `[generated]` | ✅ 2026-10-26 |
| 2 · sheetpane | installed; its generated files declared | ✅ 2026-10-25 — `llms.txt`, `llms-full.txt` |
| 3 · codelaw | installed; it has no fully generated file (docs-sync regions sit inside hand-written docs) | ✅ 2026-10-26 |
| 4 · milo | installed (Arpit, 2026-10-25: *"Lockmaster is ready to be consumed by Fux, Sheetpane, Codelaw, and Milo"*); no work system there, so the NOW hooks stay silent | ✅ 2026-10-25 |

## Blockers

None — W-06 closed 2026-10-25: `lockmaster install` exists.

## Record affected

Each repo's own records that own `.claude/hooks/*` — amended there, not here.

## Found while adopting (2026-10-25)

- The kit carried lockmaster's own `ci.yml`; `install --backup` would have moved each repo's CI aside. Removed from the kit — a repository's CI is its own (SR-ARCHITECTURE decisions 15–16 amended).
- `now-ledger.py` crashed and `require-progress.sh` nagged in a repo with no `work/NOW.md` (milo). Both are silent there now; tested.
- `install` run from the Linux VM writes the VM's python and path into `.git/config`'s merge drivers; they were re-pointed at the Mac's (`/Library/Developer/CommandLineTools/usr/bin/python3 ~/my_programs/lockmaster/src/lockmaster/merge.py`).

- fux's post-commit / post-merge / post-checkout re-index ran inside lockmaster's own git steps (a landing worktree, `main`'s checkout). lockmaster now runs a repo's gate hooks only (SR-ARCHITECTURE decision 18, `tests/test_gate_hooks.py`).
- fux registered its hooks without `python3 ` in front, so the kit's entries came in beside them: the old seven were removed by hand; fux's `tests/test_agent_hooks.py` now fails on a second spelling.
- The kit restated fux's fingerprinted rule 41 in `docket`; reworded. The kit's inbox hook read only `## Blocked on the decider` (fux's is *on Arpit*) and doubled fux's stored `age` column; both fixed.
- Not measured: how long `fux ingest --no-fetch` takes in a fresh landing worktree on the Mac (no runtime cache). The VM run was killed before it finished. Step 4 measures it; if it is minutes, the fork goes back to Arpit.

## Hazards

- Each repo has its own concurrent sessions: install when its `work/NOW.md` is empty.

## Reference

- [W-06](../../archive/open/W-06-install.md) (closed) · [SR-ARCHITECTURE](../../records/0101_architecture.md) decisions 14–15
