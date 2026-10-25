# Security policy

## Reporting a vulnerability

**Please don't open a public issue.** Report it privately through GitHub instead:

1. Go to the repository's **Security** tab.
2. Choose **Report a vulnerability**.

You'll get an acknowledgement within 5 working days, and a fix or a plan within 30 days of confirming the issue.

## What counts

lockmaster runs git commands and the checks a repository configures, and
writes to `main`, so these are in scope:

- a landing that **loses** a commit, a file or a branch not already in `main`;
- a crafted `lockmaster.toml`, branch name or path that makes lockmaster **run
  a command it was not configured to run**, or write outside the repository;
- a claim that lets a change land paths **outside** it;
- anything in a published package that differs from what's in this repository.

## Supported versions

lockmaster has no release yet. Fixes go into `main`.
