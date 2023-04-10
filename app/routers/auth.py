from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from app.db.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.token import TokenData
from datetime import timedelta
from app.crud import user
from app.schemas.user import UserCreate
from app.schemas.common import ApiResponse

router = APIRouter()
@router.post("/login", response_model=ApiResponse, tags=["auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = crud.user.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer"))

@router.post("/signup", response_model=ApiResponse, tags=["auth"])
async def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = crud.user.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = crud.user.create_user(db, user_data)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )

    return ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer"))