from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Source
from app.schemas.schemas import SourceResponse, SourceListResponse

router = APIRouter(prefix="/sources", tags=["Sources"])

@router.get("", response_model=List[SourceResponse])
def list_sources(
    platform_type: Optional[str] = Query(None, description="Filter by platform type: telegram, web_portal, etc."),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive sources"),
    db: Session = Depends(get_db)
):
    """List all supported Cambodian recruitment job sources"""
    query = db.query(Source)

    if platform_type:
        query = query.filter(Source.platform_type == platform_type.strip().lower())

    if is_active is not None:
        query = query.filter(Source.is_active == is_active)

    return query.order_by(Source.id.asc()).all()

@router.get("/{id}", response_model=SourceResponse)
def get_source_detail(id: int, db: Session = Depends(get_db)):
    """Get details of a specific job source"""
    source = db.query(Source).filter(Source.id == id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Source with ID {id} not found",
                    "details": []
                }
            }
        )
    return source

