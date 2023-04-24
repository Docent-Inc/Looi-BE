from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.db.database import get_db
from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.security import create_access_token, decode_access_token, create_refresh_token
from app.schemas.response.token import TokenData
from app.schemas.request.token import TokenRefresh
from datetime import timedelta
from app.schemas.common import ApiResponse
from app.auth.user import get_user_by_email, create_user, authenticate_user
from app.schemas.request.user import UserCreate, PasswordChangeRequest
from app.core.security import get_current_user, verify_password, get_password_hash
from app.schemas.response.user import User, PasswordChangeResponse

router = APIRouter(prefix="/auth")
access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
refresh_token_expires = timedelta(days=7)  # 리프레시 토큰 만료 기간을 설정합니다.

@router.post("/signup", response_model=ApiResponse, tags=["Auth"])
async def signup(
    user_data: UserCreate, # UserCreate 스키마를 사용합니다.
    db: Session = Depends(get_db), # 데이터베이스 세션을 받아옵니다.
):
    existing_user = get_user_by_email(db, email=user_data.email) # 이메일로 사용자를 조회합니다.
    if existing_user: # 사용자가 존재하면
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered", # 에러 메시지를 반환합니다.
        )

    new_user = create_user(db, user_data) # 사용자를 생성합니다.
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token( # 액세스 토큰을 생성합니다.
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token( # 리프레시 토큰을 생성합니다.
        data={"sub": new_user.email}, expires_delta=refresh_token_expires
    )
    return ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer", refresh_token=refresh_token))

@router.post("/login", response_model=ApiResponse, tags=["Auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), # OAuth2PasswordRequestForm을 사용합니다.
    db: Session = Depends(get_db),
):
    user = authenticate_user( # 이메일과 비밀번호로 사용자를 조회합니다.
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
        max_age=access_token_expires.total_seconds() # 쿠키의 만료 기간을 설정합니다.
    )
    return response
@router.post("/refresh-token", response_model=ApiResponse, tags=["Auth"])
async def refresh_token(
    token_refresh: TokenRefresh, # TokenRefresh 스키마를 사용합니다.
    db: Session = Depends(get_db),
):
    # 리프레시 토큰이 유효한지 확인
    payload = decode_access_token(token_refresh.refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    email: str = payload.get("sub") # 이메일을 가져옵니다.
    user = get_user_by_email(db, email=email) # 이메일로 사용자를 조회합니다.
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 새로운 액세스 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return ApiResponse(success=True, data=TokenData(access_token=access_token, token_type="bearer"))

@router.post("/setpw", response_model=ApiResponse, tags=["Auth"])
async def change_password(
    password_change_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 증명되지 않은 사용자는 비밀번호를 변경할 수 없습니다.
    if not verify_password(password_change_request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # 새로운 비밀번호를 해시합니다.
    current_user.hashed_password = get_password_hash(password_change_request.new_password)
    db.add(current_user)
    db.commit()

    return ApiResponse(success=True, data=PasswordChangeResponse(message="Password changed successfully"))
