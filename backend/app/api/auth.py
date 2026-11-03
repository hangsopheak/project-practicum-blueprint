from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.models import User, Profile
from app.schemas.schemas import (
    UserRegisterRequest,
    RegisterResponse,
    UserLoginRequest,
    LoginResponse,
    UserResponse,
    OTPSendRequest,
    OTPSendResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
)
from app.services.email_service import send_email_otp, verify_email_otp

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """EP-02: Register a new candidate user"""
    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "CONFLICT",
                    "message": "Email is already registered in the system",
                    "details": []
                }
            }
        )

    # Create new user
    new_user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role="user"
    )
    db.add(new_user)
    db.flush()

    # Automatically initialize a blank profile
    default_profile = Profile(
        user_id=new_user.id,
        full_name=data.email.split("@")[0].capitalize(),
        experience_level="entry",
        preferred_role="Candidate",
        preferred_location="Phnom Penh"
    )
    db.add(default_profile)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(subject=str(new_user.id))

    return {
        "user_id": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        "token": token
    }

@router.post("/login", response_model=LoginResponse)
def login(
    data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """EP-03: Authenticate user and receive Bearer JWT token"""
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid email or password",
                    "details": []
                }
            }
        )

    token = create_access_token(subject=str(user.id))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }


@router.post("/otp/send", response_model=OTPSendResponse)
def send_otp(
    data: OTPSendRequest,
    db: Session = Depends(get_db)
):
    """EP-14: Generate and send 6-digit verification code to email"""
    otp_record, code = send_email_otp(db=db, email=data.email, purpose=data.purpose)

    return {
        "message": "OTP verification code sent to your email",
        "email": data.email,
        "expires_in_seconds": 600,
        "dev_code": code  # Available for local development / testing demo
    }


@router.post("/otp/verify", response_model=OTPVerifyResponse)
def verify_otp(
    data: OTPVerifyRequest,
    db: Session = Depends(get_db)
):
    """EP-15: Verify 6-digit OTP code and issue JWT session"""
    is_valid, user, token, message = verify_email_otp(
        db=db,
        email=data.email,
        code=data.code,
        purpose=data.purpose
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": message,
                    "details": []
                }
            }
        )

    return {
        "message": message,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        } if user else None
    }
