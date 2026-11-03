from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, JobListing, SavedJob
from app.schemas.schemas import SavedJobResponse
from app.api.jobs import format_job_item

router = APIRouter(prefix="/saved-jobs", tags=["Saved Jobs & Bookmarks"])

@router.get("", response_model=List[SavedJobResponse])
def get_saved_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """EP-10: Retrieve list of candidate's bookmarked job listings"""
    saved_records = (
        db.query(SavedJob)
        .filter(SavedJob.user_id == current_user.id)
        .order_by(SavedJob.created_at.desc())
        .all()
    )

    results = []
    for record in saved_records:
        if record.job and record.job.is_active:
            results.append(
                SavedJobResponse(
                    id=record.id,
                    job=format_job_item(record.job),
                    saved_at=record.created_at
                )
            )
    return results

@router.post("/{job_id}", status_code=status.HTTP_201_CREATED)
def save_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """EP-11: Bookmark a job listing for future review"""
    # 1. Verify job exists
    job = db.query(JobListing).filter(JobListing.id == job_id, JobListing.is_active == True).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Job listing with ID {job_id} not found",
                    "details": []
                }
            }
        )

    # 2. Check if already saved
    existing = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id
    ).first()

    if not existing:
        new_save = SavedJob(user_id=current_user.id, job_id=job_id)
        db.add(new_save)
        db.commit()

    return {"message": "Job bookmarked successfully", "job_id": job_id}

@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
def unsave_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """EP-12: Remove a job bookmark"""
    record = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Bookmark record not found",
                    "details": []
                }
            }
        )

    db.delete(record)
    db.commit()

    return {"message": "Job bookmark removed successfully", "job_id": job_id}
