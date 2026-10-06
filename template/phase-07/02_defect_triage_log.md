# Phase 7.2 — Defect Triage Log

**Objective:** Record every bug you find, fix the important ones first, and be honest about what remains before the defense.

**Status:** In Progress / Submitted · **Last updated:** [STUDENT INPUT: YYYY-MM-DD]

## Done When

- [ ] Every FAIL in Phase 7.1 has a bug entry
- [ ] No Critical bug is open
- [ ] Every fixed bug has a root cause, a fix commit and a re-test
- [ ] Every unfixed bug is listed under Known Issues
- [ ] No fill-in markers left (the placeholder check prints nothing)

## 1. Severity Levels

| Severity | Meaning | When to fix |
|---|---|---|
| Critical | Crash, data loss, security hole, or a Must-Have journey is blocked | Immediately, before anything else |
| Major | A feature works incorrectly, but a workaround exists | Before code freeze |
| Minor | Cosmetic issues, typos, small layout glitches | If time remains |

Fix flow: reproduce → log it here → find the root cause → fix (commit message contains the bug ID, e.g. `fix(BUG-003): ...`) → re-run the failed test → close.

## 2. Bug Triage Log

| Bug ID | Description | Severity | Steps to reproduce | Root cause | Fix implemented (commit) | Resolution date | Status |
|---|---|---|---|---|---|---|---|
| BUG-001 | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT: steps, or the TC-xx that found it] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT: Open / Fixed / Won't fix] |
| BUG-002 | | | | | | | |
| BUG-003 | | | | | | | |

## 3. Known Issues (not fixed before the defense)

These go into the limitations section of your thesis.

| Bug ID | Why it is not fixed | Workaround |
|---|---|---|
| [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
