---
type: Handoff
name: W-19
description: "Arpit, 2026-11-09: publish through the CI/CD pipeline — whose tests had failed on every push since 2026-10-26; CI made green on all six runners."
item: W-19
filed: 2026-11-09
filed_by: "Arpit (Claude Code, Opus 5.5)"
updated: 2026-11-09
updated_by: "Claude Code (Opus 5.5): built and closed in the same change"
ball: done
---

# W-19 — CI green on every runner

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `lint`: the guard replays `main`'s own line (`--first-parent`), each commit against its first parent — a resubmitted landing's refused first attempt is a branch commit, not `main`'s | three historical commits stop failing every run | ✅ |
| 2 | Ubuntu pinned to `ubuntu-24.04`: `ubuntu-latest` became 26.04, which has no Python 3.9 | the 3.9 job runs | ✅ |
| 3 | Windows, 12 failures: `block-main.py` read `C:\…` as escapes (a real gap: `git -C C:\repo commit` passed); `status`, `doctor` and `worktree-cleanup.py` print paths in the platform's form; the tests' checks are Python, not `! grep` (checks run in `cmd.exe`), TOML strings escaped, a Windows venv layout for the command's environment, the detached pickup awaited before the repository is deleted, the `sh` hook skipped | Windows 3.9 and 3.13 green | ✅ draft PR #1, run 42580433393 |

**Arpit, 2026-11-09:** *"push and publish the latest package through cicd pipeline"*.

## Goal

The release pipeline's test and lint jobs pass, so a tag can reach publishing (W-17).

## Record affected

SR-WORK-OWNERSHIP decision 7; SR-ARCHITECTURE decisions 12, 13, 17; SR-WORK-CLEANUP decision 6.
