"""
backend/app/services/matching_engine.py
=======================================
JobMatch Dual-Metric Recommendation Engine
------------------------------------------

Two independent metrics are computed and NEVER confused:

  Metric 1 – required_skill_coverage  (primary, fully transparent)
  ─────────────────────────────────────────────────────────────────
  Definition : |candidate_skills ∩ job_required_skills|
               ─────────────────────────────────────────
               |job_required_skills|

  Range      : 0.0 (no overlap) → 1.0 (all required skills matched)
  Strength   : deterministic, instantly explainable, no model needed.
  Used for   : "You have X of Y required skills" UI label.
  Note on zero-skill jobs:
    When a job lists no skills, coverage is unknown. It is ranked by
    semantic similarity only (ranking_score = semantic_similarity).
    The response field required_skill_coverage is kept at 0.0, and
    matched_skills and missing_skills are empty lists ([]).
    If min_score > 0, zero-skill jobs are excluded because their effective
    coverage is 0.

  Metric 2 – semantic_similarity  (secondary, AI-powered)
  ─────────────────────────────────────────────────────────
  Model      : paraphrase-multilingual-MiniLM-L12-v2
               (sentence-transformers, verified 117,653,760 parameters, ~118 M)
  Why this model?
    • Trained on 50+ languages including multilingual sentence embeddings.
    • Note on Khmer: Khmer is not listed in the model card's training languages;
      performance on Khmer text is measured empirically in scripts/evaluate_real_engine.py.
    • 384-dimensional embeddings are fast to compute even on CPU.
    • Sentence Transformers cosine-similarity scores on English
      text closely match human relevance judgements (STSB, SICK).
  Candidate text : concatenation of skill names + preferred_role
                   + education (whatever is stored in the profile).
  Job text       : job title + company + description.
  Metric         : cosine similarity between the two unit vectors.
  Range          : 0.0 → 1.0 (mapped via (cosine + 1) / 2).
  Score compression note:
    (cosine + 1) / 2 compresses scores, so unrelated texts score near 0.5.
    It acts as a relative ranking signal, not an absolute probability.

  Metric 3 – ranking_score  (configurable weighted combination)
  ──────────────────────────────────────────────────────────────
  Formula : ranking_score = (w_skill · C + w_semantic · S) / (w_skill + w_semantic)

  Defaults: w_skill=0.70, w_semantic=0.30
  Candidate with no skills:
    Ranked by semantic similarity only (ranking_score = semantic_similarity)
    instead of being penalized to 0.30 * semantic.
  Zero-skill jobs:
    Ranked by semantic similarity only when w_semantic > 0.0.
  Deterministic ordering:
    Results are sorted by ranking_score descending, then job.id ascending.
  The weights are not claimed to be optimal — they are a reasonable
  starting point. Callers may tune them via query parameters.

NOTE: The embedding model is loaded once and cached globally.
      Job embeddings are cached in RAM keyed by job_id with a SHA-1 text hash.
"""

from __future__ import annotations

from collections import OrderedDict
import hashlib
import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
from sqlalchemy.orm import Session, selectinload

from app.models.models import JobListing, JobSkill, Profile, ProfileSkill, Skill
from app.api.jobs import format_job_item

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Embedding model — loaded once, reused for every request
# ─────────────────────────────────────────────────────────────────────────────

_EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_embedding_model = None  # loaded lazily on first call
_model_load_failed = False  # ensures ERROR is logged only once


def _get_embedding_model():
    """
    Returns the shared SentenceTransformer model instance.
    Loaded lazily so the server starts quickly even without GPU.
    Falls back gracefully if sentence-transformers is not installed.
    """
    global _embedding_model, _model_load_failed
    if _embedding_model is not None:
        return _embedding_model
    if _model_load_failed:
        return None

    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s …", _EMBEDDING_MODEL_NAME)
        _embedding_model = SentenceTransformer(_EMBEDDING_MODEL_NAME)
        logger.info("Embedding model loaded successfully.")
    except Exception as exc:
        _model_load_failed = True
        logger.error(
            "Embedding model (%s) failed to load. Semantic similarity is disabled and ranking is skills-only. Error: %s",
            _EMBEDDING_MODEL_NAME, exc
        )
        _embedding_model = None

    return _embedding_model


# ─────────────────────────────────────────────────────────────────────────────
# Canonical Skill Normalization & Aliases
# ─────────────────────────────────────────────────────────────────────────────

SKILL_ALIASES: Dict[str, str] = {
    # JavaScript / TypeScript Ecosystem
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "react native": "react native",
    "react-native": "react native",
    "nodejs": "nodejs",
    "node.js": "nodejs",
    "node": "nodejs",
    "node js": "nodejs",
    "vue": "vue",
    "vuejs": "vue",
    "vue.js": "vue",
    "angular": "angular",
    "angularjs": "angular",
    "angular.js": "angular",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "nextjs": "next.js",
    "next.js": "next.js",
    "express": "express.js",
    "expressjs": "express.js",
    "express.js": "express.js",

    # Mobile Development
    "flutter": "flutter",
    "flutter framework": "flutter",
    "dart": "dart",
    "dart lang": "dart",
    "swift": "swift",
    "swiftui": "swiftui",
    "kotlin": "kotlin",
    "android": "android",
    "ios": "ios",

    # Backend / Languages
    "py": "python",
    "python": "python",
    "python3": "python",
    "golang": "go",
    "go lang": "go",
    "go": "go",
    "java": "java",
    "c#": "c#",
    "c sharp": "c#",
    ".net": ".net",
    "dotnet": ".net",
    "php": "php",
    "laravel": "laravel",

    # Databases & Storage
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "postgre": "postgresql",
    "mysql": "mysql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "redis": "redis",
    "sql": "sql",

    # Cloud & DevOps
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "docker": "docker",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "ci/cd": "ci/cd",
    "git": "git",
    "github": "git",

    # AI / Machine Learning
    "ml": "machine learning",
    "machine learning": "machine learning",
    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",
    "nlp": "nlp",
    "deep learning": "deep learning",
}


def normalize_skill(skill_name: str) -> str:
    """Normalize skill string to canonical form using trimming, lowercasing, and alias lookup."""
    clean = re.sub(r"\s+", " ", skill_name.strip().lower())
    return SKILL_ALIASES.get(clean, clean)


# ─────────────────────────────────────────────────────────────────────────────
# In-Memory Job Embedding Cache (SHA-1 keyed by job_id with LRU cap)
# ─────────────────────────────────────────────────────────────────────────────

MAX_CACHE_SIZE = 5000
_job_embedding_cache: OrderedDict[int, Tuple[str, np.ndarray]] = OrderedDict()


def get_job_embedding(model, job_id: int, job_text: str) -> np.ndarray:
    """Retrieves or precomputes and caches the unit-norm embedding vector for a job."""
    text_hash = hashlib.sha1(job_text.encode("utf-8")).hexdigest()
    if job_id in _job_embedding_cache:
        cached_hash, cached_vec = _job_embedding_cache[job_id]
        if cached_hash == text_hash:
            _job_embedding_cache.move_to_end(job_id)
            return cached_vec

    vec = _embed(model, job_text)
    _job_embedding_cache[job_id] = (text_hash, vec)
    _job_embedding_cache.move_to_end(job_id)
    if len(_job_embedding_cache) > MAX_CACHE_SIZE:
        _job_embedding_cache.popitem(last=False)
    return vec


def warm_job_embeddings(db: Session, batch_size: int = 32) -> int:
    """
    Encodes all active primary jobs in batches with model.encode(list, batch_size=32, normalize_embeddings=True)
    and populates the in-memory cache.
    """
    model = _get_embedding_model()
    if model is None:
        logger.warning("Cannot warm job embeddings: model is not available.")
        return 0

    active_jobs = (
        db.query(JobListing)
        .filter(JobListing.is_active == True, JobListing.duplicate_of.is_(None))
        .all()
    )
    if not active_jobs:
        return 0

    jobs_to_encode: List[int] = []
    texts_to_encode: List[str] = []
    hashes: List[str] = []

    for job in active_jobs:
        jt = _build_job_text(job)
        th = hashlib.sha1(jt.encode("utf-8")).hexdigest()
        if job.id in _job_embedding_cache and _job_embedding_cache[job.id][0] == th:
            continue
        jobs_to_encode.append(job.id)
        texts_to_encode.append(jt)
        hashes.append(th)

    if not texts_to_encode:
        return len(_job_embedding_cache)

    vectors = model.encode(
        texts_to_encode,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    for job_id, th, vec in zip(jobs_to_encode, hashes, vectors):
        _job_embedding_cache[job_id] = (th, vec.astype(np.float32))
        _job_embedding_cache.move_to_end(job_id)
        if len(_job_embedding_cache) > MAX_CACHE_SIZE:
            _job_embedding_cache.popitem(last=False)

    logger.info("Warmed embeddings for %d active jobs.", len(texts_to_encode))
    return len(texts_to_encode)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _compute_skill_coverage(
    candidate_skills: set[str],
    job_skills: set[str],
) -> float:
    """
    Metric 1 — required_skill_coverage with canonical alias normalization.

    Returns the fraction of the job's required skills that the candidate possesses.
    Returns 0.0 when the job has no listed skills.
    """
    if not job_skills:
        return 0.0

    cand_norm = {normalize_skill(x) for x in candidate_skills}
    job_norm = {normalize_skill(x) for x in job_skills}

    matched = cand_norm & job_norm
    return len(matched) / len(job_norm)


def _embed(model, text: str) -> np.ndarray:
    """Produce a unit-norm embedding vector for *text* using *model*."""
    vec = model.encode(text, normalize_embeddings=True)
    return vec.astype(np.float32)


def _compute_semantic_similarity(
    candidate_text: str,
    job_text: str,
    candidate_emb: Optional[np.ndarray] = None,
    job_id: Optional[int] = None,
) -> float:
    """
    Metric 2 — semantic_similarity (normalised to [0, 1]).
    Supports pre-encoded candidate embeddings and cached job embeddings for sub-millisecond execution.
    """
    model = _get_embedding_model()
    if model is None or not candidate_text.strip() or not job_text.strip():
        return 0.0

    try:
        if candidate_emb is not None:
            emb_candidate = candidate_emb
        else:
            emb_candidate = _embed(model, candidate_text)

        if job_id is not None:
            emb_job = get_job_embedding(model, job_id, job_text)
        else:
            emb_job = _embed(model, job_text)

        # Guard: reject NaN/inf vectors that could corrupt the dot product
        if not (np.all(np.isfinite(emb_candidate)) and np.all(np.isfinite(emb_job))):
            logger.warning("Non-finite embedding vector detected; returning 0.0")
            return 0.0

        # Both vectors are unit-norm → dot product = cosine ∈ [-1, 1]
        raw_cosine = float(np.dot(emb_candidate, emb_job))

        if not math.isfinite(raw_cosine):
            logger.warning("Non-finite cosine similarity (%s); returning 0.0", raw_cosine)
            return 0.0

        # Normalise: map [-1, 1] → [0, 1]
        normalised = (raw_cosine + 1.0) / 2.0
        return max(0.0, min(1.0, normalised))

    except Exception as exc:
        logger.warning("Semantic similarity computation failed: %s", exc)
        return 0.0


def _build_candidate_text(profile: Optional[Profile], skills: List[str]) -> str:
    """
    Builds a plain-text representation of the candidate for embedding.
    Combines skill names, preferred role, and education level.
    """
    parts: List[str] = []
    if skills:
        parts.append("Skills: " + ", ".join(skills))
    if profile:
        if profile.preferred_role:
            parts.append("Role: " + profile.preferred_role)
        if profile.education:
            parts.append("Education: " + profile.education)
    return ". ".join(parts)


def _build_job_text(job: JobListing) -> str:
    """
    Builds a plain-text representation of the job for embedding.
    Combines title, company, and description.
    """
    parts: List[str] = [job.title, job.company]
    if job.description:
        parts.append(job.description)
    return ". ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Main public function
# ─────────────────────────────────────────────────────────────────────────────

def compute_ai_recommendations(
    user_id: int,
    db: Session,
    min_score: int = 0,
    min_ranking: float = 0.0,
    w_skill: float = 0.70,
    w_semantic: float = 0.30,
) -> List[Dict[str, Any]]:
    """
    Computes job recommendations for *user_id* using two independent metrics.

    Parameters
    ----------
    user_id     : ID of the authenticated candidate.
    db          : Active SQLAlchemy database session.
    min_score   : Minimum required_skill_coverage × 100 to include a job
                  (0 = include all jobs, 80 = only jobs where candidate
                   covers ≥ 80 % of required skills).
                  Zero-skill jobs have coverage 0.0 and are excluded when min_score > 0.
    min_ranking : Minimum ranking_score (0.0 to 1.0) to include a job.
    w_skill     : Weight for required_skill_coverage in ranking_score.
                  Must be between 0.0 and 1.0. Default 0.70.
    w_semantic  : Weight for semantic_similarity in ranking_score.
                  Must be between 0.0 and 1.0. Default 0.30.

    Returns
    -------
    List of recommendation dicts, sorted by ranking_score descending, then job.id ascending.
    """
    # ── 1. Fetch candidate's skills ──────────────────────────────────────
    candidate_skill_rows = (
        db.query(Skill.name)
        .join(ProfileSkill, ProfileSkill.skill_id == Skill.id)
        .filter(ProfileSkill.profile.has(user_id=user_id))
        .all()
    )
    candidate_skill_names: List[str] = [r[0] for r in candidate_skill_rows]
    candidate_skills_lower: set[str] = {s.strip().lower() for s in candidate_skill_names}
    candidate_has_skills = bool(candidate_skills_lower)

    # ── 2. Fetch candidate's profile (for semantic text) ─────────────────
    candidate_profile: Optional[Profile] = (
        db.query(Profile).filter(Profile.user_id == user_id).first()
    )
    candidate_text = _build_candidate_text(candidate_profile, candidate_skill_names)

    # Pre-encode candidate text ONCE using SentenceTransformers for maximum speed
    model = _get_embedding_model()
    candidate_emb = (
        _embed(model, candidate_text)
        if (model is not None and candidate_text.strip())
        else None
    )

    # Pre-compute canonical normalized set for candidate
    candidate_skills_normalized: set[str] = {
        normalize_skill(s) for s in candidate_skills_lower
    }

    # ── 3. Fetch all active job listings (eager-load skills to prevent N+1) ──
    active_jobs: List[JobListing] = (
        db.query(JobListing)
        .options(
            selectinload(JobListing.skills).selectinload(JobSkill.skill)
        )
        .filter(
            JobListing.is_active == True,
            JobListing.duplicate_of.is_(None)
        ).all()
    )
    if not active_jobs:
        return []

    # ── 4. Score each job ────────────────────────────────────────────────
    results: List[Dict[str, Any]] = []

    for job in active_jobs:
        job_skill_names_raw: List[str] = [
            js.skill.name for js in job.skills if js.skill
        ]
        job_skills_lower: set[str] = {s.strip().lower() for s in job_skill_names_raw}
        has_job_skills = bool(job_skills_lower)

        # ── Zero-skill jobs guard ──
        if not has_job_skills:
            # If min_score > 0, exclude zero-skill jobs as coverage is unknown (0.0)
            if min_score > 0:
                continue

            job_text = _build_job_text(job)
            semantic = _compute_semantic_similarity(
                candidate_text, job_text, candidate_emb=candidate_emb, job_id=job.id
            )
            # Rank by semantic similarity only (if w_semantic > 0, else 0.0)
            ranking = semantic if w_semantic > 0.0 else 0.0

            if min_ranking > 0.0 and ranking < min_ranking:
                continue

            display_coverage = 0.0
            results.append({
                "job": format_job_item(job),
                "required_skill_coverage": display_coverage,
                "semantic_similarity": round(semantic, 4),
                "ranking_score": round(ranking, 4),
                "matched_skills": [],
                "missing_skills": [],
                "match_score": 0,
            })
            continue

        # ── Regular jobs with skills ──
        coverage = _compute_skill_coverage(candidate_skills_lower, job_skills_lower)

        # Apply min_score filter
        effective_coverage_score = int(round(coverage * 100))
        if min_score > 0 and effective_coverage_score < min_score:
            continue

        job_text = _build_job_text(job)
        semantic = _compute_semantic_similarity(
            candidate_text, job_text, candidate_emb=candidate_emb, job_id=job.id
        )

        # Ranking score:
        # If candidate has no skills, rank by semantic similarity only
        if not candidate_has_skills:
            ranking = semantic if w_semantic > 0.0 else 0.0
        else:
            weight_sum = w_skill + w_semantic
            ranking = (w_skill * coverage + w_semantic * semantic) / weight_sum

        if not math.isfinite(ranking):
            logger.warning(
                "Non-finite ranking_score for job %s (coverage=%s, semantic=%s, "
                "w_skill=%s, w_semantic=%s); defaulting to 0.0",
                job.id, coverage, semantic, w_skill, w_semantic,
            )
            ranking = 0.0

        if min_ranking > 0.0 and ranking < min_ranking:
            continue

        # Deduplicate matched and missing skills while preserving order
        matched = list(dict.fromkeys(
            s for s in job_skill_names_raw
            if normalize_skill(s) in candidate_skills_normalized
        ))
        missing = list(dict.fromkeys(
            s for s in job_skill_names_raw
            if normalize_skill(s) not in candidate_skills_normalized
        ))

        display_coverage = round(coverage, 4)

        results.append({
            "job": format_job_item(job),
            "required_skill_coverage": display_coverage,
            "semantic_similarity": round(semantic, 4),
            "ranking_score": round(ranking, 4),
            "matched_skills": matched,
            "missing_skills": missing,
            "match_score": int(round(display_coverage * 100)),
        })

    # ── 5. Sort by ranking_score descending, then job.id ascending ───────
    results.sort(key=lambda x: (-x["ranking_score"], x["job"].id))

    return results
