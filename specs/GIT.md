---
name: git
description: Enforce atomic commit discipline and precise commit message standards. Apply when staging changes, writing commit messages, reviewing what to group into a single commit, or auditing recent history for clarity. Every commit must be a coherent, standalone unit of change with a message that tells the next reader exactly what changed and why it mattered.
---

# Git

## The Commit as a Unit of Meaning

A commit is not a save point. It is a record of one decision: one fix, one feature increment, one structural change, one documentation update. Anyone reading the log should be able to reconstruct what the project was doing and why, without opening the diff.

The discipline is: before committing, identify exactly what changed and whether it represents one decision or more than one. If more than one, split.

---

## Commit Prefixes

Every commit message begins with exactly one of the following prefixes, followed by a colon and a single space.

| Prefix | Use |
|---|---|
| `feat:` | A new capability visible to the user or to another module. |
| `fix:` | A correction to broken or incorrect behavior. |
| `docs:` | Changes to documentation only — no code behavior changes. |
| `chore:` | Maintenance work with no behavior impact: dependency updates, file moves, renaming, configuration adjustments, cleanup. |

Do not invent new prefixes. Do not combine two prefixes. If a commit feels like it belongs to two categories, it should be two commits.

---

## Message Structure

### The standard form

```
<prefix>: <what changed, stated as a fact>
```

One line. No trailing period. No capitalization after the prefix unless a proper noun requires it.

The message describes the state after the commit, not the action taken to get there. "Add email field to registration form" is a state change. "Added email field" introduces unnecessary past tense. "Working on email field" describes work in progress, not a completed unit — do not commit incomplete work.

### Length and precision

The message is as short as it can be while being unambiguous. A reader should understand what changed without needing to open the diff. However, precision is not sacrificed for brevity. A message that is technically short but meaningless — `fix: bug`, `feat: update`, `chore: cleanup` — is worse than a longer, specific one.

The ceiling is one sentence. If a commit requires more than one sentence to describe, it is either doing too much and should be split, or the change is complex enough to warrant a body.

### When a body is warranted

For commits that address a non-obvious constraint, reverse a previous decision, or implement something with significant design implications, add a body after a blank line.

```
fix: skip token validation for expired anonymous sessions

Sessions created before the auth overhaul do not carry a token field.
Validating them causes a KeyError on every legacy session still active.
This check is removed once the migration to clear old sessions is complete.
```

The body explains the *why*, not the *what*. The subject line handles the *what*.

---

## What Makes a Commit Atomic

An atomic commit contains exactly the changes required to make its message true — no more, no less.

### Violations of atomicity

- A commit that fixes a bug and also refactors unrelated code. Split: one fix commit, one chore commit.
- A commit that adds a feature and fixes a bug discovered while adding it. Split: fix first, then feat.
- A commit that contains partial work — half a feature, a file with TODO placeholders, broken tests. Do not commit broken states to the main branch.
- A commit that bundles a week of changes because committing was deferred. Stage incrementally.

### Staging selectively

Use partial staging (`git add -p`) when a single file contains changes that belong to different logical units. A file that had a bug fixed and a refactor applied in the same session can be staged in two separate commits.

---

## Message Quality Reference

These examples show the difference between messages that communicate and messages that do not.

| Poor | Better |
|---|---|
| `fix: bug fix` | `fix: prevent divide-by-zero when session duration is zero` |
| `feat: new stuff` | `feat: add pagination to the user list endpoint` |
| `chore: cleanup` | `chore: remove unused imports from auth module` |
| `fix: it works now` | `fix: resolve missing foreign key constraint in tokens table` |
| `feat: working on forms` | `feat: add client-side length validation to the message field` |
| `docs: update` | `docs: document the token expiry configuration variable` |
| `chore: misc` | `chore: move static assets to match new directory structure` |

The standard is: a developer reading only the subject line should know what the repository contains after this commit that it did not contain before.

---

## Branch and History Discipline

### Do not rewrite shared history

`git rebase` and `git push --force` are tools for cleaning local history before it is shared. Once a branch is pushed and others may have it, history is immutable.

### Commit to working states

The main branch is always in a deployable state. Feature work lives on a branch until it is complete and verified. Merging incomplete work because "it mostly works" violates this.

### No merge commits for trivial integrations

When merging a short-lived feature branch that diverged only slightly from main, rebase before merging to keep the history linear and readable. Reserve merge commits for long-lived branches where the parallel history is meaningful context.
