from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# ---------------------------------------------------------
# Standard Error Envelope (Phase 3.4 Convention)
# ---------------------------------------------------------
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list = []

class ErrorResponse(BaseModel):
    error: ErrorDetail


# ---------------------------------------------------------
# Auth Schemas (EP-02, EP-03)
# ---------------------------------------------------------
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class RegisterResponse(BaseModel):
    user_id: int
    email: str
    role: str
    token: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------
# OTP Schemas (EP-14, EP-15)
# ---------------------------------------------------------
class OTPSendRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(default="login_or_verify", description="Purpose: register, login, reset, or login_or_verify")

class OTPSendResponse(BaseModel):
    message: str
    email: str
    expires_in_seconds: int
    dev_code: Optional[str] = None

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    purpose: str = Field(default="login_or_verify")

class OTPVerifyResponse(BaseModel):
    message: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


# ---------------------------------------------------------
# Profile & Skills Schemas (EP-04, EP-05)
# ---------------------------------------------------------
class ProfileBase(BaseModel):
    full_name: str
    education: Optional[str] = None
    experience_level: str = "entry"
    preferred_role: str
    preferred_location: str = "Phnom Penh"
    expected_salary: Optional[float] = None

class ProfileUpdateRequest(ProfileBase):
    skills: List[str] = []

class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    skills: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Skill Schemas (EP-06)
# ---------------------------------------------------------
class SkillResponse(BaseModel):
    id: int
    name: str
    category: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Source Schemas (Master Recruitment Sources)
# ---------------------------------------------------------
class SourceResponse(BaseModel):
    id: int
    name: str
    code: str
    platform_type: str
    url: str
    logo_url: Optional[str] = None
    is_active: bool
    scrape_interval_minutes: int
    last_scraped_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SourceListResponse(BaseModel):
    total: int
    sources: List[SourceResponse]


# ---------------------------------------------------------
# Job Listing Schemas (EP-07, EP-08)
# ---------------------------------------------------------
class JobItemResponse(BaseModel):
    id: int
    source_id: Optional[int] = None
    title: str
    company: str
    location: str
    experience_level: str
    job_type: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    salary_period: Optional[str] = "monthly"  # monthly | yearly | hourly | daily
    is_negotiable: bool = False
    # --- New fields (teacher recommendation) ---
    work_arrangement: Optional[str] = None    # on-site | hybrid | remote
    job_category: Optional[str] = "Unknown"
    job_subcategory: Optional[str] = "Unknown"
    job_level: Optional[str] = "Unknown"
    classification_confidence: Optional[float] = None
    classification_source: Optional[str] = "rule"
    status: str = "active"                    # active | expired | closed
    application_url: Optional[str] = None     # direct apply link
    company_url: Optional[str] = None         # company website
    company_logo_url: Optional[str] = None    # company logo URL
    raw_title: Optional[str] = None           # uncleaned title
    normalized_location: Optional[str] = None # standardized location for filtering
    openings: Optional[int] = 1               # total number of openings
    source_post_id: Optional[str] = None      # external platform post ID
    scraped_at: Optional[datetime] = None     # when scraper last collected this
    dedup_hash: Optional[str] = None          # MD5 fingerprint
    # -------------------------------------------
    source: str
    source_url: str
    posted_at: Optional[str] = None
    deadline: Optional[str] = None
    skills: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class JobListResponse(BaseModel):
    total: int
    jobs: List[JobItemResponse]

class JobDetailResponse(JobItemResponse):
    description: str
    created_at: Optional[datetime] = None


# ---------------------------------------------------------
# Saved Job Schemas (EP-10, EP-11)
# ---------------------------------------------------------
class SavedJobResponse(BaseModel):
    id: int
    job: JobItemResponse
    saved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# AI Recommendation Schemas (EP-09)
# ---------------------------------------------------------
class RecommendationItemResponse(BaseModel):
    job: JobItemResponse

    # ── Metric 1: transparent skill-gap metric ─────────────────────────
    required_skill_coverage: float = Field(
        ...,
        ge=0.0, le=1.0,
        description=(
            "Fraction of a job's required skills that the candidate already has. "
            "Range 0.0–1.0. 1.0 = candidate meets every listed skill."
        )
    )

    # ── Metric 2: semantic text-embedding similarity ────────────────────
    semantic_similarity: float = Field(
        ...,
        ge=0.0, le=1.0,
        description=(
            "Normalised semantic similarity between the candidate's text embedding "
            "and the job description embedding. "
            "Model: paraphrase-multilingual-MiniLM-L12-v2 (English + Khmer). "
            "Formula: (raw_cosine + 1) / 2, mapping [-1, 1] → [0, 1]. "
            "0.5 = orthogonal / unrelated; 1.0 = identical meaning. "
            "This is a ranking score, not a hiring probability."
        )
    )

    # ── Metric 3: configurable weighted combination ─────────────────────
    ranking_score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description=(
            "Normalised weighted average used for sorting: "
            "(w_skill × required_skill_coverage + w_semantic × semantic_similarity) "
            "/ (w_skill + w_semantic). "
            "Guaranteed to be in [0.0, 1.0] without clamping when both inputs "
            "are in [0.0, 1.0] and at least one weight is positive. "
            "Default weights: w_skill=0.7, w_semantic=0.3 (configurable via query params)."
        )
    )

    # ── Explainability breakdown ────────────────────────────────────────
    matched_skills: List[str] = []
    missing_skills: List[str] = []

    # ── Legacy integer percentage (kept for backwards compatibility) ────
    match_score: int = Field(
        ...,
        ge=0, le=100,
        description="Integer percentage of required_skill_coverage × 100 (backwards compat)."
    )

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Admin Scraper Schemas (EP-13)
# ---------------------------------------------------------
class ScrapeRequest(BaseModel):
    source: str = Field(
        default="all",
        description="Target source: 'all', 'telegram', 'khmer24', 'bongthom', 'jobnet', 'cambojob', 'workingna', or specific channel name."
    )
    dry_run: bool = Field(
        default=False,
        description="If true, simulates ingestion without modifying database."
    )

class ScrapeResponse(BaseModel):
    status: str
    source: str
    new_jobs_added: int
    duplicates_skipped: int = 0
    total_jobs: int
    channel: Optional[str] = None
    saved_job: Optional[Dict[str, Any]] = None

class AdminStatsResponse(BaseModel):
    total_candidates: int
    total_jobs: int
    total_skills: int
    active_sources: List[str]
    jobs_by_source: Dict[str, int] = {}
    telegram_channels: List[str] = []
    auto_scraper_status: str = "active"  # 'active', 'running', 'idle'
    last_scraped_at: Optional[str] = None
    next_scrape_in_minutes: Optional[int] = None
