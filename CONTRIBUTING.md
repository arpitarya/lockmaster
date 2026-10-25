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

## Pull requests

- Keep to the standard library (SR-ARCHITECTURE decision 2) and Python 3.9 syntax.
- A change to an owned component updates its record in the same commit; the
  commit guard (`scripts/sr-guard.sh`) checks this.
- Never add a forced git operation (SR-ARCHITECTURE decision 11).

Contributions are licensed under the [MIT licence](LICENSE).
