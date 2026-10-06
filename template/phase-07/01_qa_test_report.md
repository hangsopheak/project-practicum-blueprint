# Phase 7.1 — QA Test Report

**Objective:** Produce the evidence that your system works, and where it does not. This report becomes the Testing & Evaluation chapter of your thesis.

**Status:** In Progress / Submitted · **Last updated:** [STUDENT INPUT: YYYY-MM-DD]

## Done When

- [ ] Every Must-Have feature (F-xx) and journey (UJ-xx) has at least one functional test
- [ ] Sections 2 and 3 contain at least 10 tests combined
- [ ] At least 3 device or screen configurations are tested
- [ ] Every FAIL links to a bug ID in Phase 7.2
- [ ] The metrics add up
- [ ] No fill-in markers left (the placeholder check prints nothing)

## Test Environment

| Item | Value |
|---|---|
| Commit tested | [STUDENT INPUT: commit SHA] |
| Backend and database | [STUDENT INPUT: with versions] |
| Client build | [STUDENT INPUT] |
| Test dates | [STUDENT INPUT] |

Write the Expected result before you run each test, and keep it even if the test fails: an honest FAIL is more useful than a rewritten PASS. When a test fails, log it in Phase 7.2 and write the bug ID in Status, e.g. `FAIL (BUG-004)`.

## Section 1: Functional / Happy Path Tests

| ID | Test case | Input data | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| TC-FN-01 | [STUDENT INPUT: refer to F-xx / UJ-xx] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT: PASS / FAIL] |
| TC-FN-02 | | | | | |
| TC-FN-03 | | | | | |

## Section 2: Negative & Boundary Tests

Cover empty inputs, invalid emails, values just below, at and above each limit, and SQL/XSS symbols such as `' OR 1=1 --` and `<script>alert(1)</script>`.

| ID | Test case | Input data | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| TC-NB-01 | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| TC-NB-02 | | | | | |
| TC-NB-03 | | | | | |

## Section 3: Authentication & Security Boundary Tests

Cover a protected route with no token, an expired token, a malformed token, and another user's resource (should return 403 or 404). Also check that passwords never appear in any response.

| ID | Test case | Input data | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| TC-SEC-01 | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| TC-SEC-02 | | | | | |
| TC-SEC-03 | | | | | |

## Section 4: Device & Responsive Compatibility

| ID | Device / emulator | OS version | Resolution | Orientation | Screens tested | Status |
|---|---|---|---|---|---|---|
| TC-DEV-01 | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| TC-DEV-02 | | | | | | |
| TC-DEV-03 | | | | | | |

## Test Metrics Summary

Pass rate = Passed ÷ Total × 100.

| Section | Total | Passed | Failed | Pass rate |
|---|---|---|---|---|
| 1. Functional | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| 2. Negative & boundary | | | | |
| 3. Security | | | | |
| 4. Device | | | | |
| **All** | | | | |

**Conclusion and limitations**

> [STUDENT INPUT: 3–5 sentences: what the results show, what was not tested, and why.]
