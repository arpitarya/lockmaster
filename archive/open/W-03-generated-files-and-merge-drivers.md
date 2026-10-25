---
type: Handoff
name: W-03
description: "Arpit, 2026-10-25: build step 1 of the lockmaster design — the part usable from plain git today."
item: W-03
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Claude Code (Opus 5.5), closed — built"
ball: none
closed: 2026-10-25
---

# W-03 — generated files rebuilt, never merged; three structural merge drivers

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Read `lockmaster.toml` (`[generated]`, `[merge]`) with `tomllib` or the subset reader | one config, Python 3.9+ | ✅ |
| 2 | `lockmaster regen`: restore each generated path to `main`'s and rebuild it with its command | generated files stop conflicting | ✅ |
| 3 | Merge drivers `append-newest-first`, `table-rows`, `append`, installed into `.git/config` + `.gitattributes` | two new rows never conflict | ✅ |
| 4 | Scratch-repo tests for each, under `tests/` | proof on a real git repo | ✅ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Sonnet: well-specified, mechanical, test-first.

## Goal

Two agents that each add a worklog entry, a queue row or a lesson never conflict, and a generated file is never hand-merged.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · config | `lockmaster.toml` read on Python 3.9 and 3.11+, same result; a key outside the subset is a loud error | ✅ |
| 2 · regen | `lockmaster regen` rebuilds every `[generated]` path; a failing command fails the run | ✅ |
| 3 · drivers | each driver merges two branches that both added rows, in a scratch repo, with no conflict; a true conflict still conflicts | ✅ |
| 4 · no forcing | `grep -rnE -- "--force|branch -D|reset --hard" src` prints nothing | ✅ |

## Outcome

**Closed 2026-10-25 (Claude Code, Opus 5.5) — built.** `src/lockmaster/config.py` reads `lockmaster.toml` (subset reader on 3.9–3.10; `tomllib` on 3.11+, checked against the same subset); `generated.py` is `lockmaster regen`, refusing to overwrite a generated file with uncommitted edits; `merge.py` holds the three drivers, which hand any overlap they cannot settle to `git merge-file`; `drivers.py` is `lockmaster drivers`. Tests: `tests/test_config.py`, `tests/test_regen.py` (with the no-forcing grep), `tests/test_merge.py`. The live answer is SR-ARCHITECTURE decisions 9, 10, 13.

## Blockers

None.

## Record affected

SR-ARCHITECTURE decisions 9, 10 and 13.

## Hazards

- A merge driver that silently picks one side loses data: when it cannot merge, it must exit non-zero and leave conflict markers.
- Python 3.9 has no `tomllib`; the subset reader must refuse what it does not understand.

## Reference

- [SR-ARCHITECTURE](../../records/0101_architecture.md) · fux's `src/fux/maintain/mergedriver.py` (the shape of a refusing merge driver)
