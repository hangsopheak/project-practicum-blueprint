# JobMatch Recommendation Engine — Claims Audit, Summaries, and FAQ

## 1. Engine Summaries

### 30-Word Summary
The JobMatch recommendation engine pairs candidate profiles with Cambodian job postings using a dual-metric formula: 70% normalized skill coverage and 30% sentence semantic similarity, processed locally on our own server.

### 100-Word Summary
JobMatch ranks Cambodian job opportunities for job seekers through two independent signals. The primary signal computes exact overlap across canonical technical skills (weighted at 0.70) with alias normalization. The secondary signal applies a multilingual transformer model (`paraphrase-multilingual-MiniLM-L12-v2`, 118M parameters) to measure semantic similarity between candidate profiles and job descriptions (weighted at 0.30). Embeddings are cached by job ID; a SHA-1 hash of the job text detects edited descriptions to maintain mean warm request latencies of 39.99 ms (range 36.00-48.08 ms, 20 calls, 18 jobs). The system runs locally without per-request API fees, protects user data privacy, and provides transparent matched and missing skill explanations.

### 300-Word Summary
The JobMatch recommendation engine provides personalized job recommendations for Cambodian entry-level candidates and job seekers by evaluating active vacancies against candidate profiles. Built using FastAPI, PostgreSQL, and SentenceTransformers, the architecture addresses the unique challenges of the Cambodian job market, where listings range from structured web portals to informal bilingual Telegram channels.

The scoring pipeline operates in five deterministic stages. First, the candidate's skills, preferred role, and education are extracted, and the candidate profile text is encoded once in memory. Second, active primary listings are queried with eager-loaded skill relationships to prevent redundant database queries. Third, for each listing, required skill coverage is computed by matching canonical skills through an alias dictionary that resolves common variations (such as ReactJS and React.js). Fourth, semantic similarity is calculated using cosine distance mapped to a unit interval; precomputed job vectors are retrieved from an in-memory cache keyed by job ID (where a SHA-1 hash of the job text detects edited descriptions). Vacancies lacking skill tags are ranked by semantic similarity alone. Fifth, the composite ranking score combines skill coverage (70%) and semantic similarity (30%), breaking ties deterministically by job ID.

On an empirical benchmark of 30 representative postings written by the author evaluated across 5 candidate profiles, the hybrid configuration achieved a Precision@5 of 0.76 and a Recall@5 of 0.75, matching or slightly outperforming single-signal baselines on this small set. Warm endpoint requests average mean 39.99 ms (range 36.00-48.08 ms, 20 calls, 18 jobs) including database queries and serialization. Because all calculations execute locally on self-hosted infrastructure, the engine incurs no external API fees and ensures candidate personal data remains strictly on our own server. Explainability chips clearly identify matching and missing skills for each vacancy.

---

## 2. Claims Audit Table

| Claim | Evidence | Source File | Status |
|---|---|---|:---:|
| **Warm ranking latency** | Standalone warm ranking across 30 cached jobs was about 0.5 to 1 ms (median 0.49 ms, max 1.02 ms). | `backend/scripts/latency_5runs.txt` (5 runs) | **Verified** |
| **Warm HTTP response** | Mean HTTP response time over 20 repeated calls was 39.99 ms (range 36.00-48.08 ms, 20 calls, 18 jobs) on 18 jobs in `jobmatch_db`. | `backend/scripts/benchmark_endpoint_results.txt` | **Verified** |
| **No per-request API fees** | Embeddings are computed locally using an open-weights SentenceTransformer on CPU; no third-party paid APIs are called. | `backend/app/services/matching_engine.py` | **Verified** |
| **Privacy design** | Recommendation calculations run on our own server. The engine does not send candidate profile data to external AI services. The embedding model is downloaded from Hugging Face on first start. This is a design description, not a security or legal guarantee. | Architecture inspection | **Partly verified** |
| **Khmer subset performance** | On 15 bilingual/Khmer postings written by the author, skills-only and hybrid reached Recall@5 of 0.87, while semantic-only reached 0.77. The postings contain English skill words, so this does not show the model understands Khmer. | `backend/scripts/evaluation_results.txt` | **Verified** |
| **Khmer pre-training claim** | The Hugging Face model card for `paraphrase-multilingual-MiniLM-L12-v2` does not list Khmer among its training languages. | Hugging Face model card | **Verified** |
| **Model parameter count** | Exactly 117,653,760 parameters (~118 M), not 278 M. | Inspected model weights via PyTorch | **Verified** |
| **P@5 & R@5 results** | Any hybrid weighting from 0.2/0.8 to 0.9/0.1 gave P@5 = 0.76 and R@5 = 0.75 on 30 representative postings. | `backend/scripts/evaluation_results.txt` | **Verified** |
| **Hybrid vs baselines** | On the 30-job benchmark, Hybrid (0.76) scored 0.04 higher (one relevant job for one profile) than Skills-Only (0.72) and Semantic-Only (0.72). | `backend/scripts/evaluation_results.txt` | **Verified** |
| **Zero SQL N+1 regressions** | Database statements counted during execution equal exactly 5, independent of job count (tested on 10 and 100 jobs). | `backend/tests/test_recommendations.py` | **Verified** |
| **Automated test coverage** | 58 automated tests passed cleanly. | `pytest` test suite output | **Verified** |
| **Comparison with Jev** | Jev is a cloud-hosted decision classification SaaS without local vector similarity search; JobMatch uses local dense vector retrieval. | Architectural comparison | **Partly verified** (Jev API docs reviewed; Jev was not benchmarked on Cambodian data) |
| **Production scaling to 50,000 jobs** | In-memory cache capped at 5,000 entries; larger scale requires vector index like pgvector or FAISS. | Technical estimate | **Unverified** (we did not test datasets above 100 jobs) |

---

## 3. Frequently Asked Questions (25 Questions)

### For Job Seekers
1. **Why is a specific job ranked first on my list?**  
   A job ranks first because it has the highest combined score from your verified skills (70%) and text similarity (30%). If you possess all required skills and your preferred role matches the job description, it receives top priority. Ties are broken by job ID. *(Source: `matching_engine.py`)*

2. **What does the match score percentage mean?**  
   The match score represents the percentage of required skills for that job that you have listed on your profile. It is a transparency signal, not your probability of being hired or receiving an interview. *(Source: `matching_engine.py`)*

3. **What profile data does the recommendation engine read?**  
   The engine only reads your selected skills, your preferred role, and your education level. It does not use your name, contact information, or account credentials. *(Source: `matching_engine.py`)*

4. **Why are some skills I know listed under "missing skills"?**  
   If an employer writes a skill in a format not recognized by our dictionary, or if you have not explicitly checked that skill in your profile, the system treats it as unverified and marks it missing. Updating your profile resolves this. *(Source: `matching_engine.py`)*

5. **How does the system treat jobs that list no skills?**  
   Jobs without listed skills have their skill coverage set to 0.0 and are ranked by semantic text similarity alone (`ranking = semantic`). Because they are not penalized for missing skills, a zero-skill job with high semantic similarity can rank higher than a job where the candidate matches only some skills (e.g. 0.70 vs 0.56 with default weights). They are excluded entirely if you set a minimum score filter above 0% (`min_score > 0`). *(Source: `matching_engine.py`)*

6. **Can I hide jobs that do not match my minimum expectations?**  
   Yes. You can provide a `min_score` parameter (0–100) to filter by skill coverage, or a `min_ranking` parameter (0.0–1.0) to exclude low overall scores. *(Source: `recommendations.py`)*

### For Developers
7. **How do I change the default weights between skills and semantic similarity?**  
   Default weights can be modified in the function signature of `compute_ai_recommendations` and the FastAPI query parameters in `recommendations.py`. API clients can also override them dynamically per request via `?w_skill=0.5&w_semantic=0.5`. *(Source: `recommendations.py`)*

8. **How do I add new skill synonyms to the normalization dictionary?**  
   Add the alias mapping to `SKILL_ALIASES` in `backend/app/services/matching_engine.py`. Keys should be lowercase, trimmed strings pointing to canonical names. *(Source: `matching_engine.py`)*

9. **How can I swap the SentenceTransformer model?**  
   Update `_EMBEDDING_MODEL_NAME` in `matching_engine.py` to another Hugging Face model identifier. Clear `_job_embedding_cache` so that embeddings are recomputed with the new dimension and weights. *(Source: `matching_engine.py`)*

10. **How does the embedding cache handle job description edits?**  
    The cache stores a SHA-1 hash of the job text alongside the vector. When a job description is updated, the hash check fails, prompting the engine to recompute the vector and update the entry without key accumulation. *(Source: `matching_engine.py`)*

11. **How can I avoid cold latency on application startup?**  
    Set `WARM_EMBEDDINGS_ON_STARTUP=True` in your environment configuration. During startup, the application runs `warm_job_embeddings()`, pre-encoding all active jobs in batches of 32. This also initializes and loads the embedding model into RAM. *(Source: `main.py`, `matching_engine.py`)*

12. **How does the system prevent N+1 SQL queries when loading skills?**  
    The query uses SQLAlchemy's `selectinload(JobListing.skills).selectinload(JobSkill.skill)`. This loads all related entities across two queries rather than querying the database for each job, executing exactly 5 SQL statements. *(Source: `matching_engine.py`)*

13. **How would we scale the engine to 50,000 jobs?**  
    At 50,000 jobs, linear in-memory scanning becomes inefficient. The next step is storing the 384-dimensional vectors in PostgreSQL using the `pgvector` extension with an HNSW index. *(Source: Technical Roadmap)*

### For Employers and Recruiters
14. **Does the engine evaluate candidate age, gender, or ethnicity?**  
    No. The candidate text builder extracts only skills, target role, and education level. Demographic attributes are never accessed or stored in the vector representation. *(Source: `matching_engine.py`)*

15. **Can the ranking favor candidates based on address or location?**  
    No. Candidate location is not factored into the recommendation score. Location filtering is handled separately as a search filter in the job discovery catalog. *(Source: `matching_engine.py`)*

16. **Is the recommendation score a hiring or screening decision?**  
    No. The score is solely a discovery ordering mechanism for job seekers. It does not provide automated candidate evaluation or make candidate selection decisions for employers. *(Source: `docs/HOW_RECOMMENDATIONS_WORK.md`)*

17. **Why might our company's posting rank lower for relevant candidates?**  
    If your job posting lists skills that the candidate lacks, their partial coverage lowers their overall composite score. Conversely, postings with no listed skills are evaluated on semantic text similarity alone and may rank higher than partial matches, but are excluded if the seeker filters with `min_score > 0`. Explicitly tagging recognized technical skills ensures accurate matching. *(Source: `matching_engine.py`)*

### For Partners, Academic Reviewers, and Viva Committee
18. **How was the recommendation engine evaluated?**  
    The engine was evaluated on a benchmark dataset of 30 representative Cambodian postings written by the author and 5 student profiles using Precision@5 and Recall@5. Ground truth relevance labels were defined by the author. *(Source: `backend/scripts/evaluate_real_engine.py`)*

19. **What if the hybrid model does not beat single-signal baselines?**  
    On our 30-job benchmark, any hybrid weighting from 0.2/0.8 to 0.9/0.1 gave the same P@5 (0.76) and R@5 (0.75), while single-signal baselines scored 0.72. A difference of 0.04 represents one job for one profile; the hybrid approach provides a balanced safeguard rather than an overwhelming statistical gain on this small set. *(Source: `backend/scripts/evaluation_results.txt`)*

20. **Does the model support Khmer and how do we know?**  
    The model card for `paraphrase-multilingual-MiniLM-L12-v2` does not list Khmer among its training languages. Its capability was measured empirically on 15 Khmer/bilingual Telegram jobs in our test set, reaching Recall@5 of 0.87. However, those jobs contain English technical words, so this does not show the model understands Khmer language grammar. *(Source: `backend/scripts/evaluation_results.txt`)*

21. **What is Jev and why was it not adopted?**  
    Jev is a cloud-hosted decision classification model suited for structured categorical choices. It does not perform vector cosine search over unstructured vacancy descriptions, requires paid US-hosted cloud subscriptions, and introduces network latency. *(Source: Phase 5 Technical Assessment)*

22. **What do the 58 automated tests verify and what do they NOT verify?**  
    The tests verify mathematical invariants, weight limits, error codes, N+1 query prevention (5 statements), caching mechanics, and zero-skill edge cases. They do not verify subjective human satisfaction or real-world user application rates. *(Source: `backend/tests/test_recommendations.py`)*

23. **Why are cosine similarities scaled with `(cosine + 1) / 2`?**  
    Raw cosine similarities can range from -1.0 to 1.0. The linear transformation maps them strictly to [0.0, 1.0] so they can be combined safely with skill coverage fractions without negative values. *(Source: `matching_engine.py`)*

24. **Why is the candidate text encoded only once per request?**  
    Encoding text through a transformer network takes approximately 18 ms on CPU (derived: end-to-end minus ranking-only, median 17.75 ms). By encoding the candidate profile once before the job loop, the engine avoids repeating this operation for each job listing. *(Source: `matching_engine.py`, `backend/scripts/latency_5runs.txt`)*

25. **What happens if the SentenceTransformer model fails to load?**  
    The engine catches the exception, logs a single ERROR, and sets the model reference to `None`. Semantic similarities default to 0.0, and rankings fall back gracefully to skill coverage alone without crashing. *(Source: `matching_engine.py`)*

---

## 4. Weak Points & Honest Critical Responses

1. **Weak Point: Small Benchmark Dataset (30 Postings, 5 Profiles)**  
   *Critical Challenge*: A sample size of 30 jobs is too small to draw statistically significant conclusions.  
   *Honest Response*: We agree. The benchmark is an indicative test set to ensure the hybrid formula behaves rationally across representative profiles, not an exhaustive statistical proof.  
   *Next Step*: Expand the dataset to 200 labeled postings with multi-annotator agreement (Cohen's Kappa).

2. **Weak Point: Khmer Language Training Uncertainty**  
   *Critical Challenge*: MiniLM was not explicitly trained on Khmer text according to its model card.  
   *Honest Response*: Correct. Khmer subword tokenization relies on SentencePiece overlap with multilingual corpora. The 15 Khmer postings tested contained English technical words.  
   *Next Step*: Fine-tune a dedicated Khmer language model (such as KhmerBERT) or benchmark with localized word embeddings.

3. **Weak Point: Un-tuned Arbitrary Weights (0.70 / 0.30)**  
   *Critical Challenge*: The 70/30 weight split was selected by intuition rather than hyperparameter optimization.  
   *Honest Response*: True. We did not perform Bayesian optimization or grid-search tuning on an independent validation set. Our sensitivity sweep shows that weights between 0.2 and 0.9 produce identical results on this small set.  
   *Next Step*: Collect user click-through and application logs to optimize weights using Learning-to-Rank (LambdaMART).

4. **Weak Point: Zero-Skill Jobs Ranking Higher Than Partial Match Jobs**  
   *Critical Challenge*: A zero-skill job with semantic score 0.70 ranks higher (0.70) than a job with 50% skill coverage and the same 0.70 semantic score (which scores 0.56).  
   *Honest Response*: This is true in our code. Because zero-skill jobs have unknown coverage, they are scored on semantic similarity alone without a skill coverage penalty.  
   *Next Step*: Introduce a default coverage penalty or require explicit skill tagging before ingestion.

5. **Weak Point: Subjective Author Ground Truth Labels**  
   *Critical Challenge*: Ground truth labels were created by the system author, introducing potential confirmation bias.  
   *Honest Response*: This is a legitimate limitation. The author created both the profiles and the relevance labels for the academic defense.  
   *Next Step*: Conduct a user study with independent RUPP undergraduate students evaluating recommendations blind.

---

## 5. One-Page Cheat Sheet

### Core Formula
$$\text{Ranking Score} = \frac{w_{\text{skill}} \cdot \text{Coverage} + w_{\text{semantic}} \cdot \text{Semantic}}{w_{\text{skill}} + w_{\text{semantic}}}$$
*Defaults*: $w_{\text{skill}} = 0.70$, $w_{\text{semantic}} = 0.30$. Both scores in $[0.0, 1.0]$.

### Model & Specifications
- **Model Name**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Embedding Dimensions**: 384 dimensions (unit-normalized)
- **Verified Parameters**: 117,653,760 (~118 M parameters)
- **Score Normalization**: $\text{Semantic} = (\cos(\theta) + 1.0) / 2.0$

### Pipeline Order
1. Fetch candidate skills & text representation
2. Pre-encode candidate text into 384-dimensional vector
3. Query active primary jobs (`duplicate_of IS NULL`) with `selectinload` (5 SQL statements)
4. Score loop:
   - Zero-skill jobs: rank by semantic only (`coverage = 0.0`)
   - Regular jobs: compute coverage $\rightarrow$ apply `min_score` $\rightarrow$ lookup/compute semantic $\rightarrow$ compute ranking score $\rightarrow$ apply `min_ranking`
   - Generate deduplicated `matched_skills` & `missing_skills`
5. Deterministic sort: `ranking_score DESC, job.id ASC`

### Key Measured Numbers (With Output Sources)
- **Warm HTTP request latency (18 jobs, `jobmatch_db`)**: mean **39.99 ms** (range 36.00-48.08 ms, 20 calls, 18 jobs) *(Source: `backend/scripts/benchmark_endpoint_results.txt`)*
- **Cold HTTP request latency (18 jobs, `jobmatch_db`)**: **11,371.58 ms** *(Source: `backend/scripts/benchmark_endpoint_results.txt`)*
- **Warm in-memory ranking (30 jobs, 5 runs)**: **median = 0.49 ms** (min = 0.49 ms, max = 1.02 ms; about 0.5 to 1 ms) *(Source: `backend/scripts/latency_5runs.txt`)*
- **Cold job text encoding (30 jobs, 5 runs)**: **median = 525.5 ms** (min = 504.3 ms, max = 906.2 ms) *(Source: `backend/scripts/latency_5runs.txt`)*
- **Warm end-to-end scoring (30 jobs, 5 runs)**: **median = 18.24 ms** (min = 17.66 ms, max = 29.01 ms; candidate encoding ~18 ms derived: end-to-end minus ranking-only) *(Source: `backend/scripts/latency_5runs.txt`)*
- **Precision@5 (All 30 jobs)**: **0.76** *(Source: `backend/scripts/evaluation_results.txt`)*
- **Recall@5 (All 30 jobs)**: **0.75** *(Source: `backend/scripts/evaluation_results.txt`)*
- **Khmer subset Recall@5 (15 jobs)**: **0.87** *(Source: `backend/scripts/evaluation_results.txt`)*
- **Khmer theoretical P@5 cap**: **0.44** (calculation: $(2+2+2+3+2)/25 = 11/25 = 0.44$)
- **Automated tests passing**: **58 / 58 passed** *(Source: `pytest` test suite)*
