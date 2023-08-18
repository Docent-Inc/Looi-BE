from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.auth.kakaoOAuth2 import KAKAO_AUTH_URL, get_user_kakao, mobile_create_token, KAKAO_AUTH_URL_TEST, \
    get_user_kakao_test
from app.db.database import get_db
from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.security import create_access_token, decode_access_token, create_token
from app.schemas.response.token import TokenData, TokenDataInfo
from app.schemas.request.token import TokenRefresh
from datetime import timedelta
from app.schemas.common import ApiResponse
from app.auth.user import get_user_by_email, create_user, authenticate_user, changeNickName, changePassword, deleteUser, \
    user_kakao
from app.schemas.request.user import UserCreate, PasswordChangeRequest, NicknameChangeRequest
from app.core.security import get_current_user, get_user_by_nickname
from app.schemas.response.user import User, PasswordChangeResponse, NicknameChangeResponse, DeleteUserResponse

router = APIRouter(prefix="/auth")

@router.post("/signup", response_model=ApiResponse, tags=["Auth"])
async def signup(
    user_data: UserCreate, # UserCreate 스키마를 사용합니다.
    db: Session = Depends(get_db), # 데이터베이스 세션을 받아옵니다.
):
    existing_user = await get_user_by_email(db, email=user_data.email) # 이메일로 사용자를 조회합니다.
    if existing_user: # 사용자가 존재하면
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered", # 에러 메시지를 반환합니다.
        )
    existing_user = await get_user_by_nickname(db, nickname=user_data.nickname)  # 닉네임으로 사용자를 조회합니다.
    if existing_user:  # 사용자가 존재하면
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NickName already registered",  # 에러 메시지를 반환합니다.
        )
    new_user = await create_user(db, user_data) # 사용자를 생성합니다.
    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(new_user.email) # 토큰을 생성합니다.
    return ApiResponse(
        success=True,
        data=TokenDataInfo(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="bearer",
            user_email=user_data.email,
            user_password=user_data.password,
            user_nickname=user_data.nickname,
        )
    )

@router.post("/login", response_model=ApiResponse, tags=["Auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), # OAuth2PasswordRequestForm을 사용합니다.
    db: Session = Depends(get_db),
):
    user = await authenticate_user( # 이메일과 비밀번호로 사용자를 조회합니다.
        db, email=form_data.username, password=form_data.password
    )
    if not user: # 사용자가 존재하지 않으면
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # 에러 메시지를 반환합니다.
        )
    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email) # 토큰을 생성합니다.
    return ApiResponse(
        success=True,
        data=TokenDataInfo(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="bearer",
            user_email=user.email,
            user_password=form_data.password,
            user_nickname=user.nickname,
        )
    )
@router.post("/refresh", response_model=ApiResponse, tags=["Auth"])
async def refresh_token(
    token_refresh: TokenRefresh, # TokenRefresh 스키마를 사용합니다.
    db: Session = Depends(get_db),
):
    # 리프레시 토큰이 유효한지 확인
    payload = await decode_access_token(token_refresh.refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    email: str = payload.get("sub") # 이메일을 가져옵니다.
    user = await get_user_by_email(db, email=email) # 이메일로 사용자를 조회합니다.
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email) # 토큰을 생성합니다.
    return ApiResponse(
        success=True,
        data=TokenData(
            access_token=access_token,
            expires_in=expires_in,
            token_type="bearer"
        )
    )

@router.post("/change/password", response_model=ApiResponse, tags=["Auth"])
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 비밀번호를 변경합니다.
    await changePassword(request.current_password, request.new_password, current_user, db)
    return ApiResponse(success=True, data={"password": request.new_password})

@router.post("/change/nickname", response_model=ApiResponse, tags=["Auth"])
async def change_nickname(
    nickname_change_request: NicknameChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 닉네임을 변경합니다.
    await changeNickName(nickname_change_request.nickname, current_user, db)
    return ApiResponse(success=True, data={"nickname": nickname_change_request.nickname})

@router.delete("/delete", response_model=ApiResponse, tags=["Auth"])
async def delete_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 사용자를 삭제합니다.
    await deleteUser(current_user, db)
    return ApiResponse(success=True, data=DeleteUserResponse(message="User deleted successfully"))

@router.get("/kakao", response_model=ApiResponse, tags=["Auth"])
async def kakao():
    # 카카오 인증을 위한 URL을 반환합니다.
    return ApiResponse(success=True, data={"url": KAKAO_AUTH_URL})

@router.get("/kakao/test", response_model=ApiResponse, tags=["Auth"])
async def kakao_useapp():
    # 카카오 인증을 위한 URL을 반환합니다.
    return ApiResponse(success=True, data={"url": KAKAO_AUTH_URL_TEST})

@router.get("/kakao/callback", response_model=ApiResponse, tags=["Auth"])
async def kakao_callback(
        code: str,
        db: Session = Depends(get_db),
):
    # 카카오 로그인 콜백을 처리합니다.
    data = await get_user_kakao(code)
    user = await user_kakao(data, db)
    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email) # 토큰을 생성합니다.
    return ApiResponse(
        success=True,
        data=TokenDataInfo(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="bearer",
            user_email=data.get("kakao_account").get("email"),
            user_password=str(data.get("id")), # TODO: 카카오 로그인은 비밀번호가 없습니다. 임시로 카카오 ID를 비밀번호로 사용합니다.
            user_nickname=data.get("kakao_account").get("email")[0:data.get("kakao_account").get("email").find("@")],
        )
    )

@router.get("/kakao/callback/test", response_model=ApiResponse, tags=["Auth"])
async def kakao_callback(
        code: str,
        db: Session = Depends(get_db),
):
    # 카카오 로그인 콜백을 처리합니다.
    data = await get_user_kakao_test(code)
    user = await user_kakao(data, db)
    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email)  # 토큰을 생성합니다.
    return ApiResponse(
        success=True,
        data=TokenDataInfo(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="bearer",
            user_email=data.get("kakao_account").get("email"),
            user_password=str(data.get("id")),  # TODO: 카카오 로그인은 비밀번호가 없습니다. 임시로 카카오 ID를 비밀번호로 사용합니다.
            user_nickname=data.get("kakao_account").get("email")[0:data.get("kakao_account").get("email").find("@")],
        )
    )