from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Skill
from app.schemas.schemas import SkillResponse

router = APIRouter(prefix="/skills", tags=["Skills Taxonomy"])

@router.get("", response_model=List[SkillResponse])
def get_all_skills(db: Session = Depends(get_db)):
    """EP-06: Get master list of normalized skill tags for chip selection"""
    skills = db.query(Skill).order_by(Skill.category, Skill.name).all()
    return skills
