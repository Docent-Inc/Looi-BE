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

@router.post("/signup", response_model=ApiResponse, tags=["auth"])
async def signup(
    user_data: UserCreate, # UserCreate 스키마를 사용합니다.
    db: Session = Depends(get_db), # 데이터베이스 세션을 받아옵니다.
):
    existing_user = crud.user.get_user_by_email(db, email=user_data.email) # 이메일로 사용자를 조회합니다.
    if existing_user: # 사용자가 존재하면
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered", # 에러 메시지를 반환합니다.
        )

    new_user = crud.user.create_user(db, user_data) # 사용자를 생성합니다.
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token( # 액세스 토큰을 생성합니다.
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token( # 리프레시 토큰을 생성합니다.
        data={"sub": new_user.email}, expires_delta=refresh_token_expires
    )
    return ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer", refresh_token=refresh_token))

@router.post("/login", response_model=ApiResponse, tags=["auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), # OAuth2PasswordRequestForm을 사용합니다.
    db: Session = Depends(get_db),
):
    user = crud.user.authenticate_user( # 이메일과 비밀번호로 사용자를 조회합니다.
        db, email=form_data.username, password=form_data.password
    )
    if not user: # 사용자가 존재하지 않으면
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # 에러 메시지를 반환합니다.
        )

    access_token = create_access_token( # 액세스 토큰을 생성합니다.
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token( # 리프레시 토큰을 생성합니다.
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    response_data = ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer", refresh_token=refresh_token))
    response = JSONResponse(content=response_data.dict())
    response.set_cookie( # 쿠키에 리프레시 토큰을 저장합니다.
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=access_token_expires.total_seconds(), # 쿠키의 만료 기간을 설정합니다.
    )
    return response
@router.post("/refresh-token", response_model=ApiResponse, tags=["auth"])
async def refresh_token(
    token_refresh: TokenRefresh, # TokenRefresh 스키마를 사용합니다.
    db: Session = Depends(get_db),
):
    # 리프레시 토큰이 유효한지 확인
    payload = decode_access_token(token_refresh.refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    email: str = payload.get("sub") # 이메일을 가져옵니다.
    user = crud.user.get_user_by_email(db, email=email) # 이메일로 사용자를 조회합니다.
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 새로운 액세스 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer"))
