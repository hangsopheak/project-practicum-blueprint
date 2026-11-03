# Documentation & Verification Audit Log

## 1. Overview
This internal document records the factual verification audit for all JobMatch documentation files (`docs/*.md` and `context/phase-05/03_recommendation_evaluation_report.md`).

---

## 2. Statements Not Verified From Code or Output Files

1. **Jev Comparative Performance on Cambodian Text**:
   - *Status*: Unverified.
   - *Detail*: Jev documentation and code were analyzed architecturally, but Jev was not benchmarked on the 30 representative Cambodian postings because Jev is a proprietary cloud service requiring external credentials.
2. **50,000 Job Scaling Claims**:
   - *Status*: Unverified.
   - *Detail*: Benchmarks were executed on 18 active database jobs and 30 representative evaluation postings. Scaling behavior for 50,000 jobs is an architectural estimate that requires future indexing with `pgvector` or FAISS.
3. **Long-Term User Behavioral Conversion**:
   - *Status*: Unverified.
   - *Detail*: Test coverage measures algorithmic correctness, ranking stability, and API contracts. No production user click-through or interview conversion data exists yet.

---

## 3. Direct Code Invariants Verified

- **Candidate Profile Attributes**: Verified that `_build_candidate_text` accesses only `profile.preferred_role`, `profile.education`, and `skills`. It does not access age, gender, nationality, photos, location, or experience.
- **SQL Statement Bound**: Verified via SQLAlchemy event listeners that `compute_ai_recommendations` executes exactly 5 SQL statements.
- **Cache Replacement**: Verified that altering a job description changes its SHA-1 hash and overwrites the existing entry in `_job_embedding_cache` without key accumulation.
- **Zero-Skill Job Invariant**: Verified that a job with no skills scores `ranking = semantic`, which causes it to rank higher than a job with 50% skill coverage and identical semantic score.
