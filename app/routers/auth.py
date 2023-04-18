from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from app import crud
from app.db.database import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token  # create_refresh_token를 여기에 추가
from app.schemas.response.token import TokenData
from app.core.security import decode_access_token
from app.schemas.request.token import TokenRefresh
from datetime import timedelta
from app.crud import user
from app.schemas.request.user import UserCreate
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth")

access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
refresh_token_expires = timedelta(days=7)  # 리프레시 토큰 만료 기간을 설정합니다.

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

    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    response_data = ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer", refresh_token=refresh_token))
    response = JSONResponse(content=response_data.dict())
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=access_token_expires.total_seconds(),
    )
    return response

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
    refresh_token = create_refresh_token(
        data={"sub": new_user.email}, expires_delta=refresh_token_expires
    )
    return ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer", refresh_token=refresh_token))

@router.post("/refresh-token", response_model=ApiResponse, tags=["auth"])
async def refresh_token(
    token_refresh: TokenRefresh,
    db: Session = Depends(get_db),
):
    # 리프레시 토큰이 유효한지 확인
    payload = decode_access_token(token_refresh.refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    email: str = payload.get("sub")
    user = crud.user.get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 새로운 액세스 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer"))
