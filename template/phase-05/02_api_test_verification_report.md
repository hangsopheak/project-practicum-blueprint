# Phase 5.2 — API Test Verification Report

**Objective:** Prove that every Must-Have endpoint works against a real database before any frontend work starts.

**Golden Rule:** an endpoint must pass in your API test collection before you build a screen that uses it. A bug is much easier to find in the API alone than through the app.

**Status:** In Progress / Submitted · **Last updated:** [STUDENT INPUT: YYYY-MM-DD]

## Done When

- [ ] Every Phase 3.4 endpoint appears in the matrix
- [ ] Every Must-Have endpoint shows PASS and has at least one passing error-case test
- [ ] The test run report is saved and linked
- [ ] The test collection in `api-specs/` is committed and up to date

## 1. Test Run

| Item | Value |
|---|---|
| API testing tool | [STUDENT INPUT: e.g. Bruno, Postman, Insomnia] |
| How you ran the whole collection | [STUDENT INPUT: command or menu action] |
| Commit tested | [STUDENT INPUT: commit SHA] |
| Date | [STUDENT INPUT] |
| Report or screenshot | [STUDENT INPUT: e.g. `context/assets/evidence/phase-05-api-tests.html`] |

## 2. API Verification Matrix

| ID | Method | Route | Priority | Status | Request in `api-specs/` | Sample response (shortened) |
|---|---|---|---|---|---|---|
| EP-01 | GET | /api/v1/health | Must | [STUDENT INPUT: PASS / FAIL] | [STUDENT INPUT] | `{"status":"ok","timestamp":"..."}` |
| EP-02 | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| | | | | | | |

## 3. Negative Cases

| ID | Error case | Expected status | Status |
|---|---|---|---|
| [STUDENT INPUT: EP-xx] | [STUDENT INPUT: e.g. missing required field] | [STUDENT INPUT: e.g. 400] | [STUDENT INPUT: PASS / FAIL] |
| | | | |
