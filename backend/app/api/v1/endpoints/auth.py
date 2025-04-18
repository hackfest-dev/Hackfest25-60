from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.core.auth import authenticate_user, get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash
from app.services import user as user_service
from app.schemas.user import User, UserCreate, Token
from app.models.user import User as UserModel

router = APIRouter()

@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
def signup(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new user with name, email, username and password.
    """
    # Check if user with same email exists
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    # Check if user with same username exists
    user = user_service.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists",
        )
    
    # Hash the password
    hashed_password = get_password_hash(user_in.password)
    
    # Create new user
    user = UserModel(
        email=user_in.email,
        username=user_in.username,
        name=user_in.name,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.post("/login", response_model=Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get access token for future requests.
    """
    # Try to authenticate with username/email
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # If authentication with username fails, try with email
        user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
        if user and authenticate_user(db, user.username, form_data.password):
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # Set session cookie for logout functionality
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=True
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(
    response: Response,
    session_token: str = Cookie(None)
) -> Any:
    """
    Logout user by clearing session cookie.
    """
    response.delete_cookie(
        key="session_token",
        httponly=True,
        samesite="lax",
        secure=True
    )
    
    return {"message": "Successfully logged out"}

@router.get("/verify")
def verify_token(
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Verify access token and return user data.
    """
    return User.model_validate(current_user)

@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information.
    """
    return User.model_validate(current_user) 