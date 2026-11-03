"""
backend/app/api/recommendations.py
====================================
EP-09  GET /api/v1/recommendations
------------------------------------
Returns a ranked list of active job listings personalised for the
authenticated candidate using two independent metrics:

  1. required_skill_coverage  — primary transparent metric
  2. semantic_similarity      — AI model: paraphrase-multilingual-MiniLM-L12-v2

Both metrics feed into a configurable weighted ranking_score.
See matching_engine.py for the full formula and model justification.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User
from app.schemas.schemas import RecommendationItemResponse
from app.services.matching_engine import compute_ai_recommendations

router = APIRouter(prefix="/recommendations", tags=["AI Matching & Recommendations"])

# Minimum combined weight — prevents all ranking_scores collapsing to 0.0
_MIN_COMBINED_WEIGHT = 1e-6


def _validate_weights(w_skill: float, w_semantic: float) -> None:
    """
    Raises HTTP 422 if the provided weights would produce a degenerate ranking.

    Rules
    -----
    1. Both weights are already constrained to [0.0, 1.0] by FastAPI Query.
    2. If both are effectively zero the ranking_score formula produces 0.0
       for every job, making the sorted order arbitrary and misleading.
    """
    if (w_skill + w_semantic) < _MIN_COMBINED_WEIGHT:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_WEIGHTS",
                    "message": (
                        "w_skill and w_semantic cannot both be zero. "
                        "At least one weight must be greater than 0 so that "
                        "ranking_score produces a meaningful ordering. "
                        "Example: w_skill=0.7, w_semantic=0.3 (default)."
                    ),
                    "details": {
                        "w_skill": w_skill,
                        "w_semantic": w_semantic,
                        "combined": w_skill + w_semantic,
                        "minimum_combined": _MIN_COMBINED_WEIGHT,
                    },
                }
            },
        )


@router.get("", response_model=List[RecommendationItemResponse])
def get_recommendations(
    # ── Filter ──────────────────────────────────────────────────────────
    min_score: int = Query(
        0, ge=0, le=100,
        description=(
            "Minimum required_skill_coverage × 100 to include a job. "
            "E.g. 50 = only show jobs where the candidate covers ≥ 50% of required skills."
        )
    ),
    min_ranking: float = Query(
        0.0, ge=0.0, le=1.0,
        description=(
            "Minimum ranking_score (0.0 to 1.0) to include a job. "
            "E.g. 0.50 = only show jobs with ranking_score >= 0.50."
        )
    ),
    # ── Ranking weight controls ──────────────────────────────────────────
    w_skill: float = Query(
        0.70, ge=0.0, le=1.0,
        description=(
            "Weight for required_skill_coverage in ranking_score. Default 0.70. "
            "ranking_score = w_skill * coverage + w_semantic * semantic."
        )
    ),
    w_semantic: float = Query(
        0.30, ge=0.0, le=1.0,
        description=(
            "Weight for semantic_similarity in ranking_score. Default 0.30. "
            "ranking_score = w_skill * coverage + w_semantic * semantic."
        )
    ),
    # ── Auth & DB ────────────────────────────────────────────────────────
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **EP-09: AI Recommendations Feed**

    Returns active job listings ranked by `ranking_score`, which is the
    configurable weighted sum of:
    - `required_skill_coverage` — transparent skill-gap metric (primary)
    - `semantic_similarity` — multilingual sentence-embedding cosine similarity

    All three metrics are returned separately in the response so the client
    can display each one independently.

    **Weight validation**
    - Each weight is individually clamped to [0.0, 1.0] by FastAPI.
    - If both weights are zero the ranking is meaningless — a 422 is raised.
    """
    # Guard: both-zero weights produce ranking_score=0 for every job,
    # making the sorted order arbitrary and potentially misleading.
    _validate_weights(w_skill, w_semantic)

    return compute_ai_recommendations(
        user_id=current_user.id,
        db=db,
        min_score=min_score,
        min_ranking=min_ranking,
        w_skill=w_skill,
        w_semantic=w_semantic,
    )
