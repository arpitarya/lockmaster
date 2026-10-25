---
type: Reference
description: "Environment and tooling quirks of wherever this runs — why a command fails on THIS surface."
---

# MACHINE — the surfaces this runs on

One section per surface (a laptop, a CI runner, a Cowork bridge shell). A row
is added when something fails for a reason the code did not cause.

| surface | symptom | cause | what to type instead |
|---|---|---|---|
| macOS laptop (zsh) | `timeout: command not found` | GNU coreutils is not installed | leave `timeout` out; use the tool's own timeout |
| macOS laptop (zsh) | a script using 3.10+ syntax fails | `python3` is 3.9.6 here | keep every script and hook to Python 3.9 syntax (SR-ARCHITECTURE decision 2) |
| Cowork bridge (`device_bash`) | `rm`, `git commit`, `git worktree remove` fail with `Operation not permitted`, or leave `.git/index.lock` | the bridge cannot unlink | read-only git with `git --no-optional-locks`; commit, install and clean up on the Mac |
| Cowork bridge (file tools) | writes under `.claude/` or `.github/` are refused | remote tools may not change agent or CI config | edit `kit/`, then run `PYTHONPATH=src python3 -m lockmaster install .` on the Mac |
| Claude Code cloud session | creating a GitHub repository is refused | the session is bound to its configured repositories | create it at github.com/new, then attach it |

## Disk budget — law L2: this section is always followed

**This section binds** ([SR-LAW-2](../records/0004_LAW-2-machine-budget.md)): every session and every
agent follows it — Claude Code or Cowork, main agent or sub-agent. A number here
changes only by the decider's ruling. `.claude/hooks/disk-budget.py` reads the
`budget` row below; keep its `<n> GB` spelling.

| what | value |
|---|---|
| budget | 5 GB for the whole project — main session + every sub-agent + every worktree + build output, combined |
| past the budget | every further GB needs the decider's approval, asked before it is used: Claude Code raises a permission prompt; a Cowork session asks in chat. One yes approves one GB |
| new sub-agent or worktree | asks from 90 % of the approved ceiling |
| approvals reset | when the project is back under the budget |
| not counted | shared caches outside the repo: `~/.cargo`, the pnpm store, pip's cache |
| see it | `python3 .claude/hooks/disk-budget.py fresh` |
| at filing (2026-10-25) | lockmaster is under 1 MB — a new repository |
