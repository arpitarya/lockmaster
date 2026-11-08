---
type: Handoff
name: W-17
description: "Releases publish from a tag once the trusted publishers and GitHub environments exist; and the GitHub repository is public while decision 17 says private until 0.1.0."
item: W-17
filed: 2026-11-08
filed_by: "Claude Code (Opus 5.5), from W-08's close"
updated: 2026-11-08
updated_by: "Claude Code (Opus 5.5): v0.0.3 tagged locally"
ball: arpit
---

# W-17 — releases publish from a tag; the repository's visibility

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | The decider adds the trusted publishers on pypi.org and test.pypi.org and the `testpypi` / `pypi` GitHub environments (CONTRIBUTING.md §Releasing) | a tag can publish; no token on any machine | 🔴 decider decides |
| 2 | Push the tags `v0.0.1` (`943afe6`), `v0.0.2` (`10e6c67`) and `v0.0.3` (`6b9f3a3`), made locally 2026-11-08 — once step 1 is done; pushed earlier, each starts a pipeline that fails at TestPyPI. The pipeline must not re-upload a version PyPI already has | the releases named on GitHub | 🟡 after step 1 |
| 3 | The decider rules the repository's visibility: GitHub reports `arpitarya/lockmaster` **public** (2026-11-08), and SR-ARCHITECTURE decision 17 says it stays private until 0.1.0 (W-02) — make it private, or rule it public and amend the record | the record and GitHub agree | 🔴 decider decides |

## Goal

Decision 17 as written: a release is a tag, and only a tag publishes.

## Record affected

SR-ARCHITECTURE decision 17.
