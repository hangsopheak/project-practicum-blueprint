# Phase 5.2 — API Test Verification Report

**Objective:** Prove that every Must-Have endpoint works against a real database before any frontend work starts.

**Golden Rule:** An endpoint must pass in your API test collection before you build a screen that uses it.

**Status:** Submitted · **Last updated:** 2026-10-24

## Done When

- [x] Every Phase 3.4 endpoint appears in the matrix
- [x] Every Must-Have endpoint shows PASS and has at least one passing error-case test
- [x] The test run report is saved and verified (58/58 tests passing)
- [x] The test collection in `api-specs/` is up to date

## 1. Test Run

| Item | Value |
|---|---|
| API testing tool | Pytest (HTTPX / TestClient) + Postman/Bruno Collection |
| How you ran the whole collection | `PYTHONPATH=. tests/venv/bin/pytest tests/ -v` (70 tests) |
| Test suite result | 70 passed, 0 failed, 1 warning (OpenSSL warning on macOS) |
| Date | 2026-11-02 |
| Test collection file | `api-specs/jobmatch_api_collection.json` |

## 2. API Verification Matrix

| ID | Method | Route | Priority | Status | Request in `api-specs/` | Sample response (shortened) |
|---|:---:|---|:---:|:---:|---|---|
| EP-01 | GET | `/api/v1/health` | Must | PASS | EP-01 Health Check | `{"status":"ok","timestamp":"..."}` |
| EP-02 | POST | `/api/v1/auth/register` | Must | PASS | EP-02 Register User | `{"id":15,"email":"...","role":"user"}` |
| EP-03 | POST | `/api/v1/auth/login` | Must | PASS | EP-03 Login User | `{"access_token":"...","token_type":"bearer"}` |
| EP-04 | GET | `/api/v1/profile` | Must | PASS | EP-04 Get Profile | `{"full_name":"Dara Sok","skills":["Flutter"]}` |
| EP-05 | PUT | `/api/v1/profile` | Must | PASS | EP-05 Update Profile | `{"full_name":"Dara Sok (Updated)"}` |
| EP-06 | GET | `/api/v1/skills` | Must | PASS | EP-06 Get Skills | `[{"id":1,"name":"Flutter","category":"Mobile"}]` |
| EP-07 | GET | `/api/v1/jobs` | Must | PASS | EP-07 List Jobs | `{"total":1123,"jobs":[{"title":"Flutter Dev"}]}` |
| EP-08 | GET | `/api/v1/jobs/{id}` | Must | PASS | EP-08 Job Detail | `{"title":"...","description":"...","skills":[]}` |
| EP-09 | GET | `/api/v1/recommendations` | Must | PASS | EP-09 AI Recommendations | `[{"ranking_score":0.9415,"coverage":1.0}]` |
| EP-10 | GET | `/api/v1/saved-jobs` | Should | PASS | EP-10 Get Saved Jobs | `[{"id":1,"title":"Junior Flutter Developer"}]` |
| EP-11 | POST | `/api/v1/saved-jobs/{job_id}` | Should | PASS | EP-11 Bookmark Job | `{"message":"Job bookmarked successfully"}` |
| EP-12 | DELETE | `/api/v1/saved-jobs/{job_id}` | Should | PASS | EP-12 Remove Bookmark | `{"message":"Job removed from bookmarks"}` |
| EP-13 | POST | `/api/v1/admin/scrape` | Must | PASS | EP-13 Admin Trigger Scrape | `{"status":"completed","new_jobs_added":15}` |
| EP-14 | POST | `/api/v1/auth/otp/send` | Must | PASS | EP-14 Send Email OTP | `{"message":"OTP sent","dev_code":"..."}` |
| EP-15 | POST | `/api/v1/auth/otp/verify` | Must | PASS | EP-15 Verify Email OTP | `{"message":"OTP verified","access_token":"..."}` |
| EP-16 | GET | `/api/v1/sources` | Must | PASS | EP-16 List Sources | `[{"id":1,"name":"Internships Cambodia"}]` |
| EP-17 | GET | `/api/v1/sources/{id}` | Must | PASS | EP-17 Get Source Detail | `{"id":1,"name":"Internships Cambodia"}` |

## 3. Negative Cases

| ID | Error case | Expected status | Status | Verified Behavior |
|---|---|:---:|:---:|---|
| EP-02 | Register with invalid email format | 422 | PASS | Rejected by Pydantic validation |
| EP-03 | Login with incorrect password | 401 | PASS | Returns `INVALID_CREDENTIALS` |
| EP-04 | Access profile without Bearer token | 401 | PASS | Returns `UNAUTHORIZED` |
| EP-08 | Retrieve non-existent job ID | 404 | PASS | Returns `JOB_NOT_FOUND` |
| EP-09 | Both weights set to zero (`w_skill=0, w_semantic=0`) | 422 | PASS | Returns `INVALID_WEIGHTS` |
| EP-09 | Weight out of range (`w_skill=1.5`) | 422 | PASS | Rejected with FastAPI Query validation |
| EP-11 | Bookmark non-existent job ID | 404 | PASS | Returns `JOB_NOT_FOUND` |
| EP-13 | Candidate user attempting to trigger admin scrape | 403 | PASS | Returns `FORBIDDEN` |
| EP-13 | Unauthenticated request to admin scrape | 401 | PASS | Returns `UNAUTHORIZED` |
| EP-14 | Send OTP with invalid email format | 422 | PASS | Rejected by Pydantic EmailStr validation |
| EP-15 | Verify OTP with incorrect code | 400 | PASS | Returns `BAD_REQUEST: Invalid verification code` |
| EP-17 | Retrieve non-existent source ID | 404 | PASS | Returns `NOT_FOUND` |
| EP-15 | Verify OTP reusing an already-used code | 400 | PASS | Returns `BAD_REQUEST: No active OTP request` |
| DEDUP | Phishing fake post with same title but fake contacts | N/A | PASS | Verified in `test_dedup.py`: Contacts in real job are NEVER overwritten |
| DEDUP | Scrape duplicate post from same source/post_id twice | N/A | PASS | Verified in `test_dedup.py`: Row is updated idempotently with unique constraint |
