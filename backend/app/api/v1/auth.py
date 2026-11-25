from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.common import APIResponse
from backend.app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=APIResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email and password and issue JWT tokens."""
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please contact system administrator."
        )

    # Issue tokens
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.id, "role": user.role})

    user_dto = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        health_center_id=user.health_center_id,
        health_center_name=user.health_center.name if user.health_center else None,
        medical_registration_no=user.medical_registration_no,
        is_active=user.is_active
    )

    token_dto = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_dto
    )

    return APIResponse(success=True, data=token_dto.model_dump())


@router.post("/refresh", response_model=APIResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using valid refresh token."""
    payload = decode_token(request.refresh_token)
    user_id = payload.get("sub")
    token_type = payload.get("type")

    if not user_id or token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer active."
        )

    new_access_token = create_access_token(data={"sub": user.id, "role": user.role})

    return APIResponse(
        success=True,
        data={
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    )


@router.get("/me", response_model=APIResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile and assigned facility for the logged-in user."""
    user_dto = UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        health_center_id=current_user.health_center_id,
        health_center_name=current_user.health_center.name if current_user.health_center else None,
        medical_registration_no=current_user.medical_registration_no,
        is_active=current_user.is_active
    )
    return APIResponse(success=True, data=user_dto.model_dump())
