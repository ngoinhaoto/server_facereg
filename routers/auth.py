from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from sqlalchemy.orm import Session
from database.db import get_db
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserResponse
from crud.user import create_user, get_user_by_email, get_user_by_username, authenticate_user, get_user
from security.auth import create_access_token, Token, get_current_active_user
from security.password import verify_password, get_password_hash
from fastapi.security import OAuth2PasswordRequestForm
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
import secrets
from datetime import timedelta, datetime
from services.email_service import email_service
from models.database import PasswordReset, User
from schemas.auth import PasswordResetRequest, PasswordResetConfirm


# Add a new model for password verification
class PasswordVerifyRequest(BaseModel):
    password: str


# Add a new model for password verification response
class PasswordVerifyResponse(BaseModel):
    valid: bool


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = await run_in_threadpool(lambda: get_user_by_email(db, email=user.email))
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    db_user = await run_in_threadpool(lambda: get_user_by_username(db, username=user.username))
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    if user.password != user.password_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and password confirmation do not match",
        )

    return await run_in_threadpool(lambda: create_user(db=db, user=user))


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Redirect to token endpoint for backward compatibility
    """
    return login_for_access_token(form_data)


@router.post("/verify-password", response_model=PasswordVerifyResponse)
async def verify_current_password(
    verify_data: PasswordVerifyRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Verify if the provided password matches the current user's password
    """
    user = get_user(db, user_id=current_user.id)

    is_valid = verify_password(verify_data.password, user.hashed_password)

    return {"valid": is_valid}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request a password reset token via email"""
    # Find user by email
    user = await run_in_threadpool(lambda: get_user_by_email(db, email=request.email))
    if not user:
        # Always return success to prevent email enumeration
        return {"message": "If your email is registered, you will receive a password reset link."}

    # Generate token and expiry (1 hour from now)
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)

    # Store in database
    db_reset = PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=expiry
    )
    db.add(db_reset)
    db.commit()

    # Send email
    email_service.send_password_reset(
        background_tasks,
        user.email,
        token,
        user.username
    )

    return {"message": "If your email is registered, you will receive a password reset link."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using a valid token"""
    # Find valid token
    db_reset = db.query(PasswordReset).filter(
        PasswordReset.token == request.token,
        PasswordReset.expires_at > datetime.utcnow(),
        PasswordReset.used == False
    ).first()

    if not db_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    # Update user's password
    user = db.query(User).filter(User.id == db_reset.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.hashed_password = get_password_hash(request.new_password)

    # Mark token as used
    db_reset.used = True

    db.commit()

    return {"message": "Password reset successfully"}