# lockmaster

**Lands AI-agent changes into `main`, one at a time, without ever losing work.**

Several coding agents working in one repository collide: one commits another's
half-done files, generated files conflict, worktrees pile up, finished work
sits on branches nobody merged. lockmaster is the doorman. Each agent claims
the files it will touch, works in its own worktree and hands its change in;
lockmaster puts the changes onto `main` one at a time — only the claimed files,
generated files rebuilt, your checks run — and cleans up after each. Like a
canal lock-keeper: one boat through at a time, the water levels kept safe.

> **Status: 0.0.1, pre-alpha.** 0.0.1 holds the name on PyPI. Claims, the
> queue, landing, generated files, structural merges, the kit's hooks and
> `install` are built and tested on scratch repositories; commands and files
> may still change before 0.1.0. The design of
> record is [SR-ARCHITECTURE](records/0101_architecture.md); what is left is
> the queue in [`work/OPEN-WORK.md`](work/OPEN-WORK.md).

## Install

```bash
pip install lockmaster            # Python ≥ 3.9, no dependencies
lockmaster install .              # the work-system kit into this repository, pinned
```

## How a change moves

```text
lockmaster start W-12 --paths src/a.py src/b.py   # branch + worktree + claim
cd .claude/worktrees/W-12                          # … the agent edits only the claimed files …
lockmaster submit -m "W-12: the parser"            # joins the queue and lands it, one at a time
lockmaster queue                                   # what is waiting, landed, or red
lockmaster status                                  # sessions, changes, worktrees, disk use
lockmaster doctor                                  # stale locks, orphan worktrees, unmerged branches
```

A change that cannot land cleanly — a real conflict, a failed check — goes
**red**, is set aside so the next change still lands, and waits for its agent
or a person. lockmaster never runs `--force`, `branch -D`, `reset --hard` or
`git clean`; a worktree or branch is removed only when git itself shows nothing
in it is missing from `main`.

## What it is not

Not a new version control system: every landing is a plain git commit, and
`git log` reads the history with nothing else installed. Why not build our own,
as Anthropic did for its monorepo: [`work/compare/source-control.compare.md`](work/compare/source-control.compare.md).

## Per-repository config

```toml
# lockmaster.toml
[main]
branch = "main"

[checks]                         # name = command; every one must pass before a landing
tests = "pytest -q"

[generated]                      # path or glob = command; rebuilt on landing, never merged
"CHANGELOG.md" = "python3 scripts/gen-changelog.py"

[merge]                          # structural merges: two new rows never conflict
"work/WORKLOG.md" = "append-newest-first"
"work/OPEN-WORK.md" = "table-rows"
"work/LESSONS.md" = "append"
```

`lockmaster drivers` registers the merge drivers in `.git/config` and writes
the `[merge]` paths into `.gitattributes`; plain `git merge` uses them too.
`lockmaster install <repo>` puts the work-system kit — hooks, settings, the
`docket` skill, CI — into a repository, pinned in `.claude/lockmaster.lock`.

## Working on lockmaster

Python ≥ 3.9, standard library only.

```bash
PYTHONPATH=src python3 -m lockmaster install .   # once per clone: kit/ into .claude/ and .github/, the commit guard, the merge drivers
PYTHONPATH=src python3 -m lockmaster --help      # every command
python3 -m unittest discover tests               # the tests — scratch git repositories, one file per work item
python3 scripts/check-work-system.py  # the work-system checks
```

Agents start at [`CLAUDE.md`](CLAUDE.md). Contributions: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licence

[MIT](LICENSE).
