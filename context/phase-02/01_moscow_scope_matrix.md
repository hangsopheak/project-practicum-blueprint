# Phase 2.1 — MoSCoW Scope Matrix

**Objective:** Decide exactly what you will build, and just as importantly what you will not build. This matrix protects you from scope creep for the rest of the project.

**Status:** Submitted · **Last updated:** 2026-10-15

## Done When

- [x] Every feature has a stable ID (F-01, F-02, …), exactly one priority and a pain point
- [x] At least 3 Won't-Have items are listed

## 1. Priority Rules

| Priority | Rule |
|---|---|
| Must-Have | Without it, the core journey cannot be demonstrated at the defense. |
| Should-Have | Important, but the app still works without it. Built only once all Must-Haves are done. |
| Could-Have | Nice to have (visual polish, extras). Only if time remains. |
| Won't-Have | Explicitly out of scope for this project. Becomes "future work" in your thesis. |

## 2. MoSCoW Matrix

IDs never change. If a feature changes priority, change the Priority column and note it in Section 3.

| ID | Feature | Priority | Pain point | Why this priority |
|---|---|---|---|---|
| F-01 | User Registration & Login (email + password) | Must | PP-01 | Without an account the system cannot store a profile or compute a match score |
| F-02 | User Profile (skills, education, experience, preferred role, preferred location) | Must | PP-04 | Profile data is the input to AI matching; without it the core AI feature cannot run |
| F-03 | Job Aggregation from at least 2 external sources | Must | PP-01 | Aggregation is the entire value proposition; one source is just a normal job app |
| F-04 | Data Cleaning & Normalization pipeline (title standardization, deduplication) | Must | PP-02, PP-03 | Without this, aggregated data is noisy and the match score is inaccurate |
| F-05 | Job Search with keyword and basic filters (title, location, job type) | Must | PP-01, PP-02 | Core job-discovery feature required for the defense demo |
| F-06 | Job Detail view with application link to original source | Must | PP-01 | Users must be able to act on a listing; without a link the app is a dead end |
| F-07 | AI Job Matching — match score (%) per listing based on user profile skills | Must | PP-04 | The AI feature is the project's key differentiator and must be demonstrated at defense |
| F-08 | Personalized Job Recommendations feed (ranked by match score) | Must | PP-04 | Directly demonstrates the AI output to the user; required for defense demo |
| F-09 | Saved Jobs (bookmark a listing) | Should | PP-01 | Useful for the user flow but the app still works without it |
| F-10 | CV / Resume file upload on profile | Should | PP-04 | Enriches matching data, but skill-tag matching works without it |
| F-11 | Advanced filters (salary range, experience level, date posted) | Should | PP-02 | Improves search quality; core search still works without these extra filters |
| F-12 | Push notifications for new matching jobs | Could | PP-01 | Nice engagement feature; not needed to demonstrate core functionality |
| F-13 | AI explanation of match result ("You match because…") | Could | PP-04 | Makes the AI more transparent; match score alone is sufficient for the defense |
| F-14 | AI Career Chatbot (interview prep, career Q&A) | Won't | — | Separate product feature; explicitly excluded in project scope to manage timeline |
| F-15 | Automated CV generation | Won't | — | Out of scope; requires a separate document-generation subsystem |
| F-16 | Company profile pages | Won't | — | Not necessary for job aggregation; significantly increases scope |
| F-17 | In-app job application (apply without leaving the app) | Won't | — | Requires partnerships with job sources; applying via external link is sufficient |

## 3. Scope Changes

After this phase, scope is frozen so you can focus on building. Changes are still possible: agree each one with your advisor and note it here.

| Date | Change | Why |
|---|---|---|
| 2026-10-23 | Added Email OTP verification (EP-14: POST /api/v1/auth/otp/send, EP-15: POST /api/v1/auth/otp/verify) | Enhanced candidate verification and passwordless flow with 6-digit Email OTP |
| 2026-10-23 | Expanded JobListing schema with 7 recommended attributes (work_arrangement, salary_period, dedup_hash, etc.) | Enriched job discovery, deduplication, and candidate matching pipeline |
| 2026-11-02 | Extended F-04 (Data Cleaning & Normalization) to include TypeSafe AI Jev-powered job classification: `job_category`, `job_subcategory`, `job_level` fields with hybrid Python fallback strategy. Added 4 new additive columns to `job_listings`. New service: `backend/app/services/job_classifier.py`. Does not modify recommendation engine. | Academic advisor recommendation to improve structured job classification for thesis defense |
