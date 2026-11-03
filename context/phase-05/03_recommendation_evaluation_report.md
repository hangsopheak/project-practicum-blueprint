# Phase 5.3 — Recommendation Engine Empirical Evaluation & Ablation Study

**Author:** RETH CHAN RITH (E2) 

**Advisor:** Sopheak  
**Date:** 2026-10-24  
**Status:** Evaluation Record  

---

## 1. Executive Summary

This report documents the empirical evaluation and ablation study of the **JobMatch Cambodia Recommendation Engine**, comparing single-signal baselines (*Skills-Only* and *Semantic-Only*) against the deployed *Hybrid 0.70/0.30* configuration.

The evaluation benchmarks recommendation scores using an evaluation set of **30 representative postings written by the author** (15 English listings and 15 Khmer/English bilingual listings) evaluated across **5 candidate profiles**. Ground truth relevance labels were defined by the author.

---

## 2. Methodology & Metrics

### Metrics
1. **Precision@5 ($P@5$):** The proportion of recommended vacancies in the candidate's top-5 that are marked as relevant in the author's ground truth:
   $$P@5 = \frac{|\text{Top 5 Recommended} \cap \text{Relevant Jobs}|}{5}$$
2. **Recall@5 ($R@5$):** The proportion of all relevant vacancies in the dataset pool that were retrieved in the top-5:
   $$R@5 = \frac{|\text{Top 5 Recommended} \cap \text{Relevant Jobs}|}{|\text{Relevant Jobs}|}$$
3. **Latency ($ms$):** Measured across 5 benchmark runs reporting median, minimum, and maximum values for cold encoding, warm ranking, and warm end-to-end execution.

---

## 3. Real Engine Benchmark Results

*Evaluated with neural model `paraphrase-multilingual-MiniLM-L12-v2` via `python scripts/evaluate_real_engine.py`:*

### All 30 Representative Jobs
| System Configuration | Weights ($w_{\text{skill}} / w_{\text{sem}}$) | Precision@5 | Recall@5 | Profiles | Notes |
|---|:---:|:---:|:---:|:---:|---|
| **Skills Only** | $1.0 / 0.0$ | 0.72 | 0.72 | 5 | Scored 0.04 lower than hybrid configurations. |
| **Semantic Only** | $0.0 / 1.0$ | 0.72 | 0.72 | 5 | Scored 0.04 lower than hybrid configurations. |
| **Hybrid (Balanced)** | $0.5 / 0.5$ | 0.76 | 0.75 | 5 | Ties for best on this benchmark set. |
| **JobMatch Core (Deployed)** | **$0.7 / 0.3$** | **0.76** | **0.75** | **5** | **Ties for best on this benchmark set.** |
| **Hybrid (Skill Heavy)** | $0.9 / 0.1$ | 0.76 | 0.75 | 5 | Ties for best on this benchmark set. |

*Finding:* Any hybrid weighting from 0.2/0.8 to 0.9/0.1 gave the same P@5 (0.76) and R@5 (0.75), so this set cannot distinguish between them, and the single-signal baselines scored 0.04 lower (which corresponds to exactly one relevant job for one profile on this small set).

### Khmer / Bilingual Subset Only (15 Jobs)
| System Configuration | Weights ($w_{\text{skill}} / w_{\text{sem}}$) | Precision@5 | Recall@5 | Profiles |
|---|:---:|:---:|:---:|:---:|
| **Skills Only** | $1.0 / 0.0$ | 0.36 | 0.87 | 5 |
| **Semantic Only** | $0.0 / 1.0$ | 0.32 | 0.77 | 5 |
| **JobMatch Core (0.7/0.3)** | **$0.7 / 0.3$** | **0.36** | **0.87** | **5** |

*Analysis of Khmer Subset:*
On the 15-job Khmer subset, skills-only and hybrid reached Recall@5 of 0.87, while semantic-only reached 0.77. Because the Khmer postings in this test set contain English technical skill keywords (e.g., Flutter, Python, SQL), this result does not show that the model understands Khmer language grammar or morphology.

Furthermore, Precision@5 on this 15-job subset is mathematically capped by the number of relevant Khmer jobs per profile:
- Profile 1 (Junior Flutter): 2 relevant jobs $\rightarrow$ maximum $P@5 = 2/5 = 0.40$
- Profile 2 (Backend Python): 2 relevant jobs $\rightarrow$ maximum $P@5 = 2/5 = 0.40$
- Profile 3 (Data Analyst): 2 relevant jobs $\rightarrow$ maximum $P@5 = 2/5 = 0.40$
- Profile 4 (Fresh IT Graduate): 3 relevant jobs $\rightarrow$ maximum $P@5 = 3/5 = 0.60$
- Profile 5 (Admin / Finance): 2 relevant jobs $\rightarrow$ maximum $P@5 = 2/5 = 0.40$
$$\text{Theoretical Maximum } P@5 = \frac{2 + 2 + 2 + 3 + 2}{25} = \frac{11}{25} = 0.44$$
A score of 0.36 is near this theoretical cap of 0.44 for a 5-item recommendation list.

### Measured System Latency (5-Run Evaluation)
*Source: `backend/scripts/latency_5runs.txt` (5-run evaluation on 30 representative postings):*
- **Cold Encoding (all 30 jobs once):** median = **525.5 ms** (min = 504.3 ms, max = 906.2 ms)
- **Warm Ranking Only (candidate pre-encoded):** median = **0.49 ms** (min = 0.49 ms, max = 1.02 ms; about 0.5 to 1 ms)
- **Warm End-to-End (includes candidate encoding):** median = **18.24 ms** (min = 17.66 ms, max = 29.01 ms; candidate encoding ~18 ms derived: end-to-end minus ranking-only)

*Endpoint Latency (GET /api/v1/recommendations on PostgreSQL database `jobmatch_db` with 18 active jobs):*
- **Cold Request (empty cache):** 11,371.58 ms
- **Warm Request:** mean 39.99 ms (range 36.00-48.08 ms, 20 calls, 18 jobs)
- Includes: PostgreSQL eager queries (5 statements), candidate text encoding, cached job lookups, and JSON serialization.

---

## 4. Key Engineering Implementations

1. **Skill Synonym Normalization (`SKILL_ALIASES`):** Maps variants (`react.js`, `reactjs` $\rightarrow$ `react`; `node.js`, `node` $\rightarrow$ `nodejs`; `flutter framework` $\rightarrow$ `flutter`).
2. **In-Memory Embedding Caching:** Candidate text is encoded once per request. Precomputed job embeddings are cached in RAM keyed by `job_id` with SHA-1 text hashes and a 5,000-entry LRU cap.
3. **Cross-Source Deduplication Filter:** Filters out reposts using `JobListing.duplicate_of.is_(None)` so candidates receive primary listings.
4. **N+1 SQL Query Prevention:** Uses `selectinload(JobListing.skills).selectinload(JobSkill.skill)`, executing exactly 5 SQL queries for recommendations.

---

## 5. Known Limitations

1. **Small Benchmark Set:** The evaluation uses 30 representative postings written by the author and 5 candidate profiles. While it confirms the hybrid formula runs as expected, it does not provide statistically broad proof across all industry roles.
2. **Khmer Language Training:** Khmer is not listed in the training languages on the `paraphrase-multilingual-MiniLM-L12-v2` model card. Performance was evaluated on 15 jobs only, and those jobs contained English technical words.
3. **Zero-Skill Jobs Behavior:** When a job lists no skills, coverage is unknown and the engine ranks it by semantic similarity alone (`ranking = semantic`). In testing, a zero-skill job with a semantic score of 0.70 ranks higher (0.70) than a job with 50% skill coverage and the same 0.70 semantic score (which scores $(0.70 \times 0.50 + 0.30 \times 0.70) = 0.56$), because the zero-skill job is not penalized for missing skills. Jobs with no listed skills are ranked by semantic similarity alone and can rank above jobs where the candidate matches only some skills; all 30 benchmark jobs have skills, so this case is not covered by the benchmark.
4. **Static Skill Dictionary:** Skill normalization depends on a hardcoded dictionary. Unlisted libraries or non-standard spellings are not recognized unless manually added.

---

## 6. Privacy Statement

Recommendation calculations run on our own server. The engine does not send candidate profile data to external AI services. The embedding model is downloaded from Hugging Face on first start. This is a design description, not a security or legal guarantee.
