# Contributing to lockmaster

Thanks for helping. lockmaster is at the design stage: the most useful
contribution today is **a collision you have seen** between agents or people
sharing one repository — what happened, and what was lost or nearly lost.

## Ways to help

| you have | do this |
|---|---|
| A collision story | Open an issue: what each side did, the git commands, what went wrong |
| A bug | Open an issue with `python3 -m lockmaster --version`, the command and the repo state |
| A fix of your own | Open a pull request (below) |
| A security issue | Don't open a public issue. See [SECURITY.md](SECURITY.md) |

## Build and test

Python 3.9 or newer, nothing else.

```bash
git clone https://github.com/arpitarya/lockmaster.git
cd lockmaster
PYTHONPATH=src python3 -m lockmaster install .
python3 -m unittest discover tests
python3 scripts/check-work-system.py
```

## Releasing

Only a tag publishes; [`.github/workflows/release.yml`](.github/workflows/release.yml)
does the rest (SR-ARCHITECTURE decision 17).

```bash
python3 scripts/release.py prepare 0.1.0    # bumps lockmaster.__version__, cuts CHANGELOG's [Unreleased]
git commit -am "lockmaster 0.1.0"           # the decider, by hand — agents land through lockmaster
git tag -a v0.1.0 -m "lockmaster 0.1.0"
git push origin main v0.1.0                 # test · lint · build · verify · TestPyPI · PyPI · GitHub release
```

Running the workflow by hand (Actions → release → Run workflow) does a dry
run: everything up to and including verify, and nothing published.

**One-time setup, on the maintainer's accounts** — publishing uses PyPI trusted
publishing, so no token is stored anywhere:

1. On [pypi.org](https://pypi.org/manage/account/publishing/) and
   [test.pypi.org](https://test.pypi.org/manage/account/publishing/), add a
   pending trusted publisher: project `lockmaster`, owner `arpitarya`,
   repository `lockmaster`, workflow `release.yml`, environment `pypi`
   (on TestPyPI: `testpypi`).
2. In the GitHub repository's Settings → Environments, create `testpypi` and
   `pypi`; give `pypi` a required reviewer and limit both to tags `v*`.

## Pull requests

- Keep to the standard library (SR-ARCHITECTURE decision 2) and Python 3.9 syntax.
- A change to an owned component updates its record in the same commit; the
  commit guard (`scripts/sr-guard.sh`) checks this.
- Never add a forced git operation (SR-ARCHITECTURE decision 11).

Contributions are licensed under the [MIT licence](LICENSE).
