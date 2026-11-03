from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Profile, Skill, ProfileSkill
from app.schemas.schemas import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/profile", tags=["Candidate Profile"])

def build_profile_response(profile: Profile, db: Session) -> ProfileResponse:
    # Query attached skills
    profile_skills = (
        db.query(Skill.name)
        .join(ProfileSkill, ProfileSkill.skill_id == Skill.id)
        .filter(ProfileSkill.profile_id == profile.id)
        .all()
    )
    skill_names = [s[0] for s in profile_skills]

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        education=profile.education,
        experience_level=profile.experience_level,
        preferred_role=profile.preferred_role,
        preferred_location=profile.preferred_location,
        expected_salary=float(profile.expected_salary) if profile.expected_salary is not None else None,
        skills=skill_names,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )

@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """EP-04: Retrieve current logged-in user profile and skills"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Candidate profile not found",
                    "details": []
                }
            }
        )

    return build_profile_response(profile, db)

@router.put("", response_model=ProfileResponse)
def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """EP-05: Update candidate profile, experience, and skill tags"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id, full_name=data.full_name, preferred_role=data.preferred_role)
        db.add(profile)
        db.flush()

    # Update basic fields
    profile.full_name = data.full_name
    profile.education = data.education
    profile.experience_level = data.experience_level
    profile.preferred_role = data.preferred_role
    profile.preferred_location = data.preferred_location
    profile.expected_salary = data.expected_salary

    # Update skills
    # 1. Remove existing skill associations
    db.query(ProfileSkill).filter(ProfileSkill.profile_id == profile.id).delete()

    # 2. Add selected skills (creating them in catalog if new)
    for skill_name in data.skills:
        clean_name = skill_name.strip()
        if not clean_name:
            continue
        skill = db.query(Skill).filter(Skill.name.ilike(clean_name)).first()
        if not skill:
            skill = Skill(name=clean_name, category="General")
            db.add(skill)
            db.flush()

        db.add(ProfileSkill(profile_id=profile.id, skill_id=skill.id))

    db.commit()
    db.refresh(profile)

    return build_profile_response(profile, db)
