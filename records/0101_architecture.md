---
type: Standing Record
kind: component
name: SR-ARCHITECTURE
title: "SR-ARCHITECTURE (0101) — lockmaster lands agent changes into main one at a time, on plain git"
description: "lockmaster is a small command-line tool over plain git: an agent claims the paths it will touch, works in a throwaway worktree, and submits; lockmaster lands each change onto main one at a time — only the claimed paths, generated files rebuilt, the repo's checks run, a fast-forward commit — then removes the worktree. Nothing is ever forced; what cannot land cleanly goes red, to the decider."
status: accepted
date: 2026-10-25
feature: "the lander — claims, the queue, landing, generated files, structural merges, the kit"
owns:
  - kit
  - src
  - tests
  - pyproject.toml
  - lockmaster.toml
  - .claude/hooks/claim-guard.py
  - .claude/hooks/block-main.py
  - .claude/hooks/auto-land.py
  - scripts/release.py
  - .github/workflows/release.yml
laws: [L0, L1, L2, L3, L4, L5, L6, L7, L8, L9, L10]
timestamp: 2026-10-25T13:00:00Z
content_sha: ""
ratifies: "Arpit, 2026-10-25 (Cowork): after the land proposal and the name search — 'Let's call it a lockmaster … Now create a document. Now go to GitHub and create me a new repository for this.' → 'Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out.' → on W-02's three forks: 'All the blockers, I accept whatever is said over there.' → 'I want this to be Python only project. I don't believe we need npm.'"
---

# SR-ARCHITECTURE — lockmaster lands agent changes into main, one at a time

## §1 — For humans

**lockmaster is a doorman for `main`.** Agents never commit to `main`
themselves. Each one says which files it will touch, works in its own
throwaway folder, and hands its change in. lockmaster puts the changes onto
`main` **one at a time** — like a canal lock-keeper letting one boat through —
and cleans up after each.

**It is not a new version control system.** Every landing is an ordinary git
commit; `git log` reads the history with nothing else installed.

**It never loses work.** It never forces anything. A change that cannot land
cleanly — a real conflict, a failed check, a file that would be lost — stops
**red** and goes to the decider.

```mermaid
flowchart LR
    S["lockmaster start W-nn --paths …<br/>branch + worktree + claim"] --> W["agent edits<br/>claimed paths only"]
    W --> U["lockmaster submit<br/>joins the queue"]
    U --> R{"lockmaster run<br/>one change at a time"}
    R -->|clean| L["claimed paths onto latest main<br/>generated files rebuilt<br/>checks pass<br/>fast-forward commit"]
    L --> C["worktree + branch removed"]
    R -->|conflict / check fails| X["red → the agent, then the decider's inbox"]
```

<details>
<summary><b>ASCII twin</b></summary>

```text
   start (branch + worktree + claim) --> agent edits claimed paths --> submit (queue)
                                                                          |
                                         run: one change at a time <------+
                                           | clean: claimed paths onto latest main,
                                           |        generated files rebuilt, checks,
                                           |        fast-forward commit, worktree removed
                                           | conflict / failed check: red -> agent -> decider
```

</details>

---

## §2 — For agents

### Context

On one laptop, several agents work in one repository at once. The work
system's own logs (fux, sheetpane, codelaw, 2026-09 to 2026-10) recorded the
same failures again and again: one session's commit swept another session's
staged files; generated files (`CHANGELOG.md`, `llms-full.txt`, an index)
conflicted whenever two agents touched them; worktrees piled up until the disk
filled; finished work sat on branches nobody merged; `NOW.md` and the inbox,
edited by hand, stopped matching git. Anthropic's own answer at
30,000 merges a day was a new, server-side source-control system; at one laptop
the same ideas fit on top of git (`work/compare/source-control.compare.md`).

### Decision

**What it is**

1. **A command-line tool over plain git, not a version control system.** Every
   landing is an ordinary commit on `main`; history, blame and diff are git's.
   No lockmaster state is needed to read the repository.
2. **Python ≥ 3.9, standard library only** ([SR-LAW-4](0006_LAW-4-zero-dependencies.md)). 3.9 is the `python3` on the
   decider's Mac ([`work/MACHINE.md`](../work/MACHINE.md)); the tool and every
   hook run there unchanged. Code lives in `src/lockmaster/`; the command is
   `lockmaster` (`python3 -m lockmaster` works without installing).
3. **Its state lives inside git's own directory**, at
   `$(git rev-parse --git-common-dir)/lockmaster/` — shared by every worktree,
   never committed, gone with the clone. A change is one JSON file in
   `changes/`; the land lock and the throwaway landing worktrees live there too.

**A change**

4. **A change is a claim:** a work-item id, the paths it may touch (a file, a
   directory above it, or a glob), a branch `lm/<item>` and a worktree at
   `.claude/worktrees/<item>`, kept out of the main checkout's status through
   `info/exclude`. `lockmaster start` creates all three;
   `lockmaster claim add <path>` widens the claim.
5. **Only claimed paths land.** Anything else the branch changed, committed or
   not, is left behind and reported, never swept in. `submit` commits only the
   claimed paths in the worktree. A kit hook (`claim-guard.py`) warns — never
   refuses — when an agent writes inside a change's worktree outside its claim.
6. **`lockmaster submit` queues the change and starts `lockmaster run`
   when no lander holds the land lock;** a lander already running picks the
   change up. Nobody has to remember to land; the lock still keeps it to one
   at a time (ruled 2026-10-25, W-02).

**Landing**

7. **One lander at a time.** `lockmaster run` takes the repo's land lock (a
   `mkdir` mutex in the state directory, holding the lander's pid) and lands
   queued changes oldest first. A second lander exits and leaves the queue to
   the first. A lock whose pid is dead is stale and taken over; a change it
   left mid-landing is queued again — `main` had not moved.
8. **A landing, in order:** take the claimed paths' diff against the change's
   merge base, generated files excluded, as one commit; cherry-pick it onto the
   latest `main` in a fresh worktree in the state directory; rebuild every
   generated file (decision 9); run the repo's checks; commit — the repo's own
   commit hooks run — with the item id in a `Lockmaster-Change:` trailer;
   fast-forward `main`. **When the whole branch landed**, the landing commit
   also records the branch tip as a second parent, so git itself can prove the
   branch merged and `git branch -d` removes it ([SR-LAW-3](0005_LAW-3-never-lose-work.md)
   decision 2). `main` is fast-forwarded where it is checked out
   (`merge --ff-only`, so that checkout moves with it, and refuses to overwrite
   its local edits) or else by `update-ref` against the old value; if `main`
   moved meanwhile, the landing is redone on the new `main`, up to three times.
   Then the change's worktree and branch are removed if nothing in them can be
   lost ([SR-WORK-CLEANUP](0062_WORK-cleanup.md) decisions 1–2); what cannot
   be is kept and reported. A failed attempt's landing worktree is committed
   to its own detached HEAD before it is removed.
8a. **Edits in `main`'s checkout that are the landing's own do not stop it**
   (2026-10-28, W-11). Before the fast-forward, lockmaster compares each
   uncommitted path in `main`'s checkout that the landing changes with the
   landing's version. When every one is byte-for-byte the same — edits made in
   the checkout and landed by `save` (decision 19), or a Cowork edit another
   session committed — they are staged, which loses nothing, and git takes the
   fast-forward. When any differs, nothing is staged and the change **waits**
   (decision 11), its reason naming the differing paths, never an empty line.
   **The ledger, `work/NOW.md`, never makes a landing wait** (2026-11-07, W-10):
   it is live state, rewritten by the kit's hooks and by every landing
   ([SR-WORK-NOW](0061_WORK-now.md)), so a landing that changes it carries the
   checkout's copy instead — the landing commit is rewritten with that one file
   replaced, its parents, author and message kept. `save` once blocked itself
   this way: its worktree's row was written after its copy was taken.
9. **Generated files are never merged, only rebuilt.** Each repo lists them,
   with the command that rebuilds each, in `lockmaster.toml` `[generated]`.
   Rebuilding restores each to `main`'s version first — unless it has
   uncommitted edits, which are refused by name, never overwritten — then runs
   its command; a failing command fails the landing. `lockmaster regen` does
   the same by hand.
10. **Hand-written files with a known shape merge structurally** —
    `append-newest-first` (a worklog), `table-rows` (a queue), `append` (a
    lessons file) — as git merge drivers `lockmaster drivers` registers in
    `.git/config`, with `[merge]`'s paths written into a block of
    `.gitattributes` lockmaster owns. When both sides only inserted lines at
    the same place, both insertions are kept: the landing change's on top for
    `append-newest-first`, in landing order otherwise, and a row both sides
    added kept once for `table-rows`. Anything else goes to `git merge-file`,
    so a true conflict still conflicts. Plain `git merge` uses them too.
    **A driver names the machine that registered it** — its interpreter and
    `merge.py` paths — so it is registered only where lockmaster commits
    (2026-10-28, W-11; registered from the Cowork bridge, twice, it named the
    bridge's paths): `install` on a surface that cannot commit (decision 19)
    writes `.gitattributes` and registers nothing, every `lockmaster run`
    re-points a driver whose interpreter or `merge.py` is missing on this
    machine, and `doctor` names one.
11. **Red, never forced.** A conflict outside a structural merge, a failed
    rebuild or check, a refused commit, or local edits in `main`'s checkout
    stop that change: it is marked red
    with the reason, and the agent is told — with the inbox row
    ([SR-WORK-OPEN-QUEUE](0051_WORK-open-queue.md) rule 42's shape) ready to
    add if it cannot fix it. lockmaster never forces, deletes an unmerged
    branch, hard-resets, cleans or force-pushes
    ([SR-LAW-3](0005_LAW-3-never-lose-work.md) decision 3). **A red change is
    set aside and the next queued change lands** (ruled 2026-10-25, W-02): one
    bad change does not hold up the rest. It stays in `lockmaster queue`,
    marked red with its reason, until it is fixed and resubmitted or abandoned.
    An auto-landing (decision 20) that cannot land is **held**, not red.
    **Uncommitted edits in `main`'s checkout that the fast-forward would
    overwrite are not red either: the change is waiting** (2026-11-07, W-10;
    [SR-LAW-9](0011_LAW-9-cowork-and-claude-code-together.md) decision 4).
    The landing commit — rebuilt, checked and committed — is kept under
    `refs/lockmaster/waiting/<item>`; every `lockmaster run` (and so every
    `submit`, `save`, `pickup` and end-of-turn `sync`) looks again and, once
    those edits are committed, handed off or undone, fast-forwards it with no
    resubmit and no second run of the checks. If `main` moved meanwhile, the
    landing is redone on the new `main` (decision 8), never fast-forwarded from
    a stale base. A change queued behind a waiting one still lands. A kept
    landing waits the same way and stays open once it lands; `SessionEnd`
    finishes it instead. The checkout's edits are never touched
    ([SR-LAW-3](0005_LAW-3-never-lose-work.md)). `lockmaster status` and
    `doctor` name each uncommitted path in the checkout that a queued, waiting
    or open change claims, with the change, before it lands; the kit's
    `claim-guard.py` warns a session that edits such a path there. A session
    with no hooks (Cowork) sees only `status`, `doctor` and `queue`.
12. **Only lockmaster writes to `main`.** A kit hook (`block-main.py`) refuses
    an agent's `git commit`, `merge`, `cherry-pick`, `revert`, `am` or `rebase`
    while `main` is checked out. **A plain push of `main` passes** (ruled
    2026-10-26): every option on the hook's allow-list and no refspec that
    forces (`+`) or deletes, so the remote takes only a fast-forward of the
    landings. Any other push that would update `main` is refused, an unknown
    option included. A heredoc's body is input, not commands, and is not judged.
    lockmaster's own landing runs git inside `lockmaster`, not through the
    agent's shell tool, so it passes. The hook binds agent sessions only: the
    decider's own terminal can still commit to `main`.

**Configuration**

13. **`lockmaster.toml` at the repo root** — `[main]` (the branch), `[checks]`
    (name → command; each must pass), `[generated]` (path or glob → rebuild
    command), `[merge]` (path or glob → structural driver), and an optional
    `[land]` whose only key, `auto`, is `"on"` (the default) or `"off"`
    (decision 20). Five tables of string values, nothing else; anything outside that subset is a loud error.
    It is read with `tomllib` on Python ≥ 3.11, checked against lockmaster's
    own reader of the same subset — the reader used on 3.9–3.10 — so a file
    means the same on every Python and no dependency is added.

**Commands**

14. | command | who | what it does |
    |---|---|---|
    | `lockmaster start <item> --paths …` | agent | branch + worktree + claim |
    | `lockmaster claim add <path>` | agent | widen the claim |
    | `lockmaster submit` | agent | join the queue |
    | `lockmaster run` | `submit`, a hook, or anyone | land queued changes, one at a time |
    | `lockmaster queue` | the decider | what is waiting, landed or red |
    | `lockmaster status` | anyone | live sessions, changes, worktrees, disk use against L2's budget; `--now` prints `work/NOW.md` as it should be, `--write-now` writes it |
    | `lockmaster abandon` | agent or the decider | drop a change; remove its worktree and branch only if nothing is lost |
    | `lockmaster save -m … <path>…` | Cowork, or any session that edited `main`'s checkout | land those edits, or hand them off where this surface cannot commit (decision 19) |
    | `lockmaster pickup` | the kit's hook, or anyone | land the handoffs (decision 19) |
    | `lockmaster sync` | the kit's hook | land a session's open changes now (decision 20) |
    | `lockmaster can-commit` | anyone | whether this surface can commit (exit 0) or hands off (exit 1) |
    | `lockmaster doctor` | anyone | stale locks, orphan worktrees, unmerged branches, an installed kit that is not this lockmaster's, a waiting change and the checkout edits a change's landing would wait on |
    | `lockmaster install <repo>` | the decider | install a pinned kit into a repository |
    | `lockmaster regen` | anyone | rebuild the `[generated]` files by hand |
    | `lockmaster drivers` | the decider | register the merge drivers; write `[merge]` into `.gitattributes` |

    **`work/NOW.md` is `lockmaster status --now`'s view:** its sessions are the
    sessions' own (the kit's `now-ledger.py` adds and closes them, a Cowork
    session by hand); a resource row whose path is gone leaves; the file is
    written in one shape by every landing and by `now-ledger.py`, which writes
    through lockmaster's renderer when lockmaster is importable.

**The kit**

15. **`kit/` is what lockmaster installs into a repository:** `kit/claude/`
    (the hooks, their `settings.json`, the `docket` skill) becomes the target's
    `.claude/`, and `kit/github/` (none today) its `.github/` — a repository's
    CI is its own (decision 16; amended 2026-10-25, W-09: the kit carried
    lockmaster's own `ci.yml`, which would have replaced the target's). One source, installed —
    never three hand-copied versions. `lockmaster install` copies it, merges
    the kit's hook entries into the target's `settings.json` (the target's own
    entries and keys kept), and records the version, the kit's digest and every
    installed file's hash in `.claude/lockmaster.lock`, which `doctor` checks.
    A file the kit would replace that no earlier install wrote stops the
    install by name, or with `--backup` is moved aside first. This repository
    installs its own kit the same way; `scripts/bootstrap.py` is retired
    (2026-10-25, W-06). The kit's hooks read any repository's inbox heading and
    name no law number (2026-10-26, W-09).
16. **What stays in each repository:** its records, work items, backlog,
    worklog, lessons — the project's own papers — its CI, and its `lockmaster.toml`.

**Distribution**

17. **Python only, on PyPI only** ([SR-LAW-6](0008_LAW-6-python-only.md)):
    one package, `lockmaster`; no npm package. **The repository stays private
    until 0.1.0** — public once the core loop works (ruled 2026-10-25, W-02);
    a placeholder 0.0.1 on PyPI holds the name before then (W-08).
    **A release is a tag `v<version>`, and only a tag publishes.**
    `.github/workflows/release.yml` — lockmaster's own, never in `kit/` —
    runs the tests on Linux, macOS and Windows under Python 3.9 and 3.13 and
    the work-system checks; checks that the tag, `lockmaster.__version__` (the
    one version source) and a `CHANGELOG.md` section agree
    (`scripts/release.py check`); builds the sdist and wheel, `twine check`s
    them and confirms the wheel carries every kit file; installs the wheel
    alone on every OS and Python, installs the kit into a scratch repository
    with it and lands one change; then publishes to TestPyPI and to PyPI by
    trusted publishing (no stored token), PyPI behind the `pypi` environment's
    reviewer; then creates the GitHub release from the CHANGELOG section.
    `scripts/release.py prepare <version>` cuts a version. The wheel carries
    `kit/` as `lockmaster/kit`, so `lockmaster install` works from a pip
    install.

**The repository's own git hooks**

18. **lockmaster's own git steps run a repository's gate hooks, not its post-*
    hooks** (2026-10-26, W-09). Every git command lockmaster runs carries
    `-c core.hooksPath=<git-common-dir>/lockmaster/hooks`, where a forwarder for
    each gate hook — `pre-commit`, `prepare-commit-msg`, `commit-msg`,
    `pre-merge-commit`, `pre-rebase`, `pre-push`, `applypatch-msg`,
    `pre-applypatch` — runs the repository's own (its `core.hooksPath` or
    `.git/hooks`). So a commit guard still refuses a landing, and a post-commit,
    post-merge or post-checkout side effect does not run inside a worktree
    lockmaster is about to remove or in `main`'s checkout. **What a landing must
    produce, it produces through `[generated]`** (decision 9) — in fux, the
    committed index. A person's or an agent's own git commands are untouched.

**Every surface lands, and landing does not wait for the end** (Arpit,
2026-10-28: *"As soon as the changes are done, it should keep merging it to
main so that there aren't too many conflicts later on … If co-work can commit
it, then it should go ahead and commit it. If co-work cannot commit it, then
probably Claude Code should go ahead and commit it."*)

19. **A surface that cannot commit hands its edits to one that can** (W-11).
    `lockmaster save -m … <path>…` lands uncommitted edits made directly in
    `main`'s checkout: a change is started on the paths, the checkout's
    versions are copied into its worktree, and it is submitted (decisions 6–8,
    with 8a accepting the checkout's identical edits). It first asks whether
    this surface can commit (`surface.py`): it must be able to remove a file
    in the state directory (the Cowork bridge cannot, so git's lock files
    would stay), and the checkout must not be another machine's seen through a
    mount — git lists worktrees that do not exist here, outside this checkout,
    under the state directory's `home` (the primary checkout's path where
    lockmaster first committed, written once, else read off its changes'
    worktree paths) or
    at a `.claude/worktrees/` path: a prune from here would cut them off. Every
    git command lockmaster runs takes no optional locks, so even reading leaves
    no `index.lock` on a surface that cannot remove it. Where it cannot, `save` writes a **handoff** — one new
    file in `handoffs/` naming the paths, the message and who handed it over,
    written aside and renamed in, so nothing is removed — says so in one line,
    and exits 0: handing off is success, not a problem for the decider. The
    kit's `auto-land.py` runs `lockmaster pickup` on a Claude Code session's
    start and at the end of each of its turns — no background job
    ([SR-LAW-9](0011_LAW-9-cowork-and-claude-code-together.md) decision 2). A
    handoff's name is taken exclusively, so two written at once never
    overwrite each other, and it records each file's content digest.
    Handoffs that name a common file land together, as one change under the
    newest one's message with the earlier ones listed. Each is saved; one whose
    edits are already on `main` or reverted is dropped; one with a file
    edited after it was handed off, and not handed off again, is **held** —
    nothing lands — and said once, until that edit is handed off or undone;
    one that goes red keeps
    its one change, is reported once to that session's agent — who fixes the
    files where they are, in `main`'s checkout — and is retried on that same
    change only once those edits change. One failing handoff never stops the
    rest. A pickup re-reads the handoffs before it lets go of its lock, and
    stamps when it ran; `queue` marks a handoff older than that stamp, with no
    reason given, `MISSED`.
20. **A Claude Code session's changes land at the end of every turn** (W-11).
    The kit's `auto-land.py` exports the session's id at its start, so
    `lockmaster start` records whose change it is, and at each `Stop` starts
    `lockmaster sync --pickup` in the background — a landing runs the checks
    and rebuilds, which takes fux ten minutes, accepted (B-007), so no turn waits on it;
    what it landed, held or could not land is said at the next `Stop`. It
    lands on a surface that can commit only: every open change
    of that session (by its recorded id; only a change with none is matched by
    the worktree holding the session's directory, so standing in another
    session's worktree never lands it) that holds claimed work not on `main`
    (generated files aside; a path whose content is already `main`'s is not
    pending) is committed and landed **kept** — it stays open, and
    its worktree is brought up to the landing (a fast-forward, or a merge when
    committed paths outside the claim stayed behind), so the next turn builds
    on `main` and conflicts stay small. A kept landing that cannot land is
    **held**: the change stays open with the reason, nothing goes to the
    decider, the agent is told once per state of the change, and the next turn
    tries again. A worktree lockmaster did not create — `claude --worktree`,
    an agent's own — is **adopted** as a change claiming everything it
    changed, landed the same way, and never removed by lockmaster; once its
    owner removes it, the change is abandoned; a branch with no history in
    common with `main` is not adopted. At `SessionEnd`, in the background,
    the session's changes are landed and cleaned up as by `submit`; one with
    nothing new is finished — landed if it landed kept before, else
    abandoned — its worktree and branch removed if nothing is lost.
    Files the session wrote straight into `main`'s checkout are noted, and at
    `Stop` the agent is told once to `save` them. A `Stop` reached while
    already continuing for a `Stop` hook never blocks again: it only says.
    Two end-of-turn landings of one session never run at once: a turn's end
    skips while one runs (the next turn retries), the session's end waits for
    it ([SR-LAW-8](0010_LAW-8-parallel-requests.md)).
    `[land] auto = "off"` turns it off.

### Consequences

- Landings are serial by design: on one laptop that is the point (one build at
  a time is also what L2's budget wants), at the cost of a queue that waits.
- Two agents changing the same lines with different intent is still a
  conflict; lockmaster stops and asks, a person decides.
- Decisions 19 and 20 land work every turn: `main` sees work in progress
  that passes the checks, and a repository whose checks are slow pays that
  time at the end of each turn that changed something.
- Decisions 1–17 are built (W-03 to W-07, and the release pipeline) and
  tested on scratch repositories under `tests/`; publishing waits on the
  decider's one-time trusted-publisher setup (W-08).
- `main`'s first-parent chain is exactly the landings; an agent's own commits
  are reachable through a landing's second parent. `git log --first-parent`
  reads the landings alone.
- Distribution is PyPI alone (decision 17); a Node repository runs it through
  `python3`.

### Alternatives considered

- **A new version control system, as Anthropic built for its monorepo** —
  rejected: its own authors call it unsuitable for general use; the problem
  here is concurrency on one machine, not scale.
- **A merge queue on a forge (GitHub's)** — rejected: needs a server round trip
  per change and does not stop the local sweeps, the worktree pile-up or the
  generated-file conflicts.
- **A red change stops the queue until fixed** — rejected by the decider,
  2026-10-25 (W-02): one bad change should not hold up the rest.
- **An npm package beside PyPI** — rejected by the decider, 2026-10-25 (L6).
- **Jujutsu (`jj`) as the front end** — not rejected; held in
  `work/compare/source-control.compare.md` as the fork to reopen.

### Reference (required)

- [`kit/claude/hooks/auto-land.py`](../kit/claude/hooks/auto-land.py) and [`kit/claude/skills/landing/`](../kit/claude/skills/landing/SKILL.md) — decisions 19–20; `src/lockmaster/surface.py` (19); `land.py`'s `save`, `handoff`, `pickup`, `sync`, `adopt` (19–20), `_classify` and `_carry_ledger` (8a), `retry_waiting` and `checkout_overlaps` (11); [`tests/test_autoland.py`](../tests/test_autoland.py), [`tests/test_waiting.py`](../tests/test_waiting.py).
- [`kit/`](../kit) — decisions 5, 12 and 15; [`kit/claude/hooks/claim-guard.py`](../kit/claude/hooks/claim-guard.py) (5), [`kit/claude/hooks/block-main.py`](../kit/claude/hooks/block-main.py) (12).
- [`src/lockmaster/`](../src/lockmaster) — decisions 1–15: `land.py` (4–8, 11), `generated.py` (9), `merge.py` and `drivers.py` (10), `config.py` (13), `status.py` and `now.py` (14), `install.py` and `doctor.py` (14–15).
- [`tests/`](../tests) — one scratch-repo test file per work item that built them.
- [`lockmaster.toml`](../lockmaster.toml) — this repository's own checks and merge drivers (decision 13).
- [`.github/workflows/release.yml`](../.github/workflows/release.yml), [`scripts/release.py`](../scripts/release.py), [`pyproject.toml`](../pyproject.toml) — decision 17.

### Veto condition

**Reopen this decision if:** a landing ever needs a forced git operation, or `main` holds a commit lockmaster did not make while the block-main hook is installed.

**How to check it:** `grep -rnE -- "--force|branch -D|reset --hard|git clean" src kit` prints nothing, and `git log --first-parent --format='%h %(trailers:key=Lockmaster-Change,valueonly)' main` shows a trailer on every commit after the hook's install.

---

## References

**Records** — [SR-LAW-3](0005_LAW-3-never-lose-work.md) · [SR-LAW-4](0006_LAW-4-zero-dependencies.md) · [SR-LAW-6](0008_LAW-6-python-only.md) · [SR-WORK-CLEANUP](0062_WORK-cleanup.md) · [SR-WORK-NOW](0061_WORK-now.md) · [SR-WORK-OPEN-QUEUE](0051_WORK-open-queue.md) · [SR-LAW-2](0004_LAW-2-machine-budget.md)

**Code** — [`src/lockmaster/`](../src/lockmaster) · [`kit/`](../kit) · [`tests/`](../tests) · [`lockmaster.toml`](../lockmaster.toml)

**Project docs** — [`work/compare/source-control.compare.md`](../work/compare/source-control.compare.md) · [`work/MACHINE.md`](../work/MACHINE.md)

**External** — [Redesigning source control at Anthropic](https://www.anthropic.com/engineering/redesigning-source-control) (2026-10-13)
