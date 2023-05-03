from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.auth.kakaoOAuth2 import KAKAO_AUTH_URL, get_user_kakao
from app.db.database import get_db
from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.security import create_access_token, decode_access_token, create_token
from app.schemas.response.token import TokenData
from app.schemas.request.token import TokenRefresh
from datetime import timedelta
from app.schemas.common import ApiResponse
from app.auth.user import get_user_by_email, create_user, authenticate_user, changeNickName, changePassword, deleteUser, \
    user_kakao
from app.schemas.request.user import UserCreate, PasswordChangeRequest, NicknameChangeRequest, KakaoLoginRequest
from app.core.security import get_current_user, get_user_by_nickName, access_token_expires
from app.schemas.response.user import User, PasswordChangeResponse, NicknameChangeResponse, DeleteUserResponse

router = APIRouter(prefix="/auth")

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
    access_token, refresh_token = await create_token(new_user.email) # 토큰을 생성합니다.
    return ApiResponse(
        success=True,
        data=TokenData(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            user_email=new_user.email,
            user_password=user_data.password,
        )
    )

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
    access_token, refresh_token = await create_token(user.email) # 토큰을 생성합니다.
    response_data = ApiResponse(
        success=True,
        data=TokenData(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            user_email=user.email,
            user_password=form_data.password,
        )
    )
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
    # TODO: refresh_token기능 작동 미확인
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
    return ApiResponse(
        success=True,
        data=TokenData(
            access_token=access_token,
            token_type="bearer")
    )

@router.post("/change/password", response_model=ApiResponse, tags=["Auth"])
async def change_password(
    password_change_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 비밀번호를 변경합니다.
    # TODO : 비밀번호 리턴해줘서 키체인에 저장할 수 있도록 하는 로직 필요
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

@router.post("/kakao", response_model=ApiResponse, tags=["Auth"])
async def kakao():
    # 카카오 인증을 위한 URL을 반환합니다.
    return ApiResponse(success=True, data={"url": KAKAO_AUTH_URL})

@router.post("/kakao/callback", response_model=ApiResponse, tags=["Auth"])
async def kakao_callback(
        request: KakaoLoginRequest,
        db: Session = Depends(get_db),
):
    # 카카오 로그인 콜백을 처리합니다.
    data = await get_user_kakao(request)
    user = user_kakao(data, db)
    access_token, refresh_token = await create_token(user.email)
    return ApiResponse(
        success=True,
        data=TokenData(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            user_email=data.get("kakao_account").get("email"),
            user_password=str(data.get("id")),
        )
    )