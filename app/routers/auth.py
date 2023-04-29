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
from app.auth.user import get_user_by_email, create_user, authenticate_user, changeNickName, changePassword, deleteUser
from app.schemas.request.user import UserCreate, PasswordChangeRequest, NicknameChangeRequest
from app.core.security import get_current_user, verify_password, get_password_hash, get_user_by_nickName
from app.schemas.response.user import User, PasswordChangeResponse, NicknameChangeResponse, DeleteUserResponse

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

    existing_user = get_user_by_nickName(db, nickName=user_data.nickName)  # 닉네임으로 사용자를 조회합니다.
    if existing_user:  # 사용자가 존재하면
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NickName already registered",  # 에러 메시지를 반환합니다.
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

@router.post("/change/password", response_model=ApiResponse, tags=["Auth"])
async def change_password(
    password_change_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 비밀번호를 변경합니다.
    changePassword(db, current_user, password_change_request)
    return ApiResponse(success=True, data=PasswordChangeResponse(message="Password changed successfully"))

@router.post("/change/nickname", response_model=ApiResponse, tags=["Auth"])
async def change_nickname(
    nickname_change_request: NicknameChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 닉네임을 변경합니다.
    changeNickName(nickname_change_request.nickname, current_user, db)
    return ApiResponse(success=True, data=NicknameChangeResponse(message="Nickname changed successfully"))

@router.delete("/delete", response_model=ApiResponse, tags=["Auth"])
async def delete_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 사용자를 삭제합니다.
    deleteUser(current_user, db)
    return ApiResponse(success=True, data=DeleteUserResponse(message="User deleted successfully"))