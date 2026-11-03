from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.models.models import JobListing, Skill, JobSkill
from app.schemas.schemas import JobListResponse, JobItemResponse, JobDetailResponse

router = APIRouter(prefix="/jobs", tags=["Job Discovery"])

def format_job_item(job: JobListing) -> JobItemResponse:
    skill_names = [js.skill.name for js in job.skills if js.skill]
    return JobItemResponse(
        id=job.id,
        source_id=job.source_id,
        title=job.title,
        company=job.company,
        location=job.location,
        experience_level=job.experience_level,
        job_type=job.job_type,
        salary_min=float(job.salary_min) if job.salary_min is not None else None,
        salary_max=float(job.salary_max) if job.salary_max is not None else None,
        salary_currency=job.salary_currency,
        is_negotiable=job.is_negotiable,
        work_arrangement=job.work_arrangement,
        job_category=job.job_category,
        job_subcategory=job.job_subcategory,
        job_level=job.job_level,
        classification_confidence=job.classification_confidence,
        classification_source=job.classification_source,
        company_logo_url=job.company_logo_url,
        company_url=job.company_url,
        application_url=job.application_url,
        status=job.status,
        source=job.source,
        source_url=job.source_url,
        posted_at=str(job.posted_at) if job.posted_at else None,
        deadline=str(job.deadline) if job.deadline else None,
        skills=skill_names
    )

@router.get("", response_model=JobListResponse)
def list_jobs(
    search: Optional[str] = Query(None, description="Search keyword in title, company, or description"),
    source: Optional[str] = Query(None, description="Filter by source name/portal"),
    source_id: Optional[int] = Query(None, description="Filter by master source ID"),
    experience_level: Optional[str] = Query(None, description="Filter: entry, junior, mid, senior"),
    job_category: Optional[str] = Query(None, description="Filter by job category (e.g. Information Technology)"),
    location: Optional[str] = Query(None, description="Filter by location (e.g. Phnom Penh)"),
    min_salary: Optional[float] = Query(None, description="Minimum expected salary"),
    since: Optional[str] = Query(None, description="Filter jobs created/seen since timestamp (ISO 8601 or YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """EP-07: Search and filter aggregated jobs with pagination (returns unique main jobs only)"""
    query = db.query(JobListing).filter(
        JobListing.is_active == True,
        JobListing.duplicate_of.is_(None)
    )

    if since:
        try:
            clean_since = since.strip().replace(" ", "+").replace("Z", "+00:00")
            since_dt = datetime.fromisoformat(clean_since)
            query = query.filter(JobListing.created_at >= since_dt)
        except Exception:
            pass

    if source_id is not None:
        query = query.filter(JobListing.source_id == source_id)

    if source:
        query = query.filter(JobListing.source.ilike(f"%{source.strip()}%"))

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                JobListing.title.ilike(term),
                JobListing.company.ilike(term),
                JobListing.description.ilike(term),
                JobListing.skills.any(JobSkill.skill.has(Skill.name.ilike(term)))
            )
        )

    if experience_level:
        query = query.filter(JobListing.experience_level == experience_level.strip().lower())

    if job_category:
        query = query.filter(JobListing.job_category.ilike(f"%{job_category.strip()}%"))

    if location:
        query = query.filter(JobListing.location.ilike(f"%{location.strip()}%"))

    if min_salary is not None:
        query = query.filter(
            or_(
                JobListing.salary_max >= min_salary,
                JobListing.is_negotiable == True
            )
        )

    total = query.count()
    jobs = query.order_by(JobListing.created_at.desc()).offset(skip).limit(limit).all()

    items = [format_job_item(j) for j in jobs]
    return JobListResponse(total=total, jobs=items)

@router.get("/{id}", response_model=JobDetailResponse)
def get_job_detail(id: int, db: Session = Depends(get_db)):
    """EP-08: Get detailed job view with full requirements and external apply link"""
    job = db.query(JobListing).filter(JobListing.id == id, JobListing.is_active == True).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Job listing with ID {id} not found",
                    "details": []
                }
            }
        )

    item = format_job_item(job)
    return JobDetailResponse(
        **item.model_dump(),
        description=job.description,
        created_at=job.created_at
    )
