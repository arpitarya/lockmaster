# lockmaster

**Lands AI-agent changes into `main`, one at a time, without ever losing work.**

Several coding agents working in one repository collide: one commits another's
half-done files, generated files conflict, worktrees pile up, finished work
sits on branches nobody merged. lockmaster is the doorman. Each agent claims
the files it will touch, works in its own worktree and hands its change in;
lockmaster puts the changes onto `main` one at a time — only the claimed files,
generated files rebuilt, your checks run — and cleans up after each. Like a
canal lock-keeper: one boat through at a time, the water levels kept safe.

> **Status: design, not yet built.** The design of record is
> [SR-ARCHITECTURE](records/0101_architecture.md); the build order is the queue
> in [`work/OPEN-WORK.md`](work/OPEN-WORK.md).

## How a change moves

```text
lockmaster start W-12 --paths src/a.py src/b.py   # branch + worktree + claim
# … the agent edits only the claimed files …
lockmaster submit                                  # joins the queue
lockmaster run                                     # lands queued changes, one at a time
lockmaster queue                                   # what is waiting, landed, or red
```

A change that cannot land cleanly — a real conflict, a failed check — goes
**red** and waits for a person. lockmaster never runs `--force`, `branch -D`,
`reset --hard` or `git clean`.

## What it is not

Not a new version control system: every landing is a plain git commit, and
`git log` reads the history with nothing else installed. Why not build our own,
as Anthropic did for its monorepo: [`work/compare/source-control.compare.md`](work/compare/source-control.compare.md).

## Per-repository config

```toml
# lockmaster.toml
[main]
branch = "main"

[checks]
run = ["pytest -q"]

[generated]                      # rebuilt on landing, never merged
"CHANGELOG.md" = "python3 scripts/gen-changelog.py"

[merge]                          # structural merges: two new rows never conflict
"work/WORKLOG.md" = "append-newest-first"
"work/OPEN-WORK.md" = "table-rows"
```

## Working on lockmaster

Python ≥ 3.9, standard library only.

```bash
python3 scripts/bootstrap.py          # once per clone: installs kit/ into .claude/ and .github/, the commit guard
python3 -m lockmaster --help          # the stub names its commands
python3 -m unittest discover tests    # the tests
python3 scripts/check-work-system.py  # the work-system checks
```

Agents start at [`CLAUDE.md`](CLAUDE.md). Contributions: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licence

[MIT](LICENSE).
