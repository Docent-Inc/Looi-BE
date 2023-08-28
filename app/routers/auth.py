from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.feature.kakaoOAuth2 import KAKAO_AUTH_URL, get_user_kakao, KAKAO_AUTH_URL_TEST, \
    get_user_kakao_test
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import decode_access_token, create_token
from app.schemas.response import TokenData, ApiResponse, KakaoTokenData
from app.schemas.request import TokenRefresh, UserUpdateRequest
from app.feature.user import get_user_by_email, create_user, authenticate_user, changeNickName, changePassword, \
    deleteUser, user_kakao, changeMbti, updateUser
from app.schemas.request import UserCreate, PasswordChangeRequest, NicknameChangeRequest, \
    MbtiChangeRequest
from app.core.security import get_current_user, get_user_by_nickname
from app.schemas.response import User

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
            detail=4001,
        )
    existing_user = get_user_by_nickname(db, nickname=user_data.nickname) # 닉네임으로 사용자를 조회합니다.
    if existing_user:  # 사용자가 존재하면
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4002,
        )
    new_user = await create_user(db, user_data) # 사용자를 생성합니다.
    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(new_user.email) # 토큰을 생성합니다.
    return ApiResponse(
        data=TokenData(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="bearer",
        ),
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
            detail=4003,
        )
    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email) # 토큰을 생성합니다.
    return ApiResponse(
        data=TokenData(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="Bearer",
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4004,
        )
    email: str = payload.get("sub") # 이메일을 가져옵니다.
    user = await get_user_by_email(db, email=email) # 이메일로 사용자를 조회합니다.
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4005,
        )
    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email) # 토큰을 생성합니다.
    return ApiResponse(
        data=TokenData(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="bearer",
        )
    )

@router.post("/change/password", response_model=ApiResponse, tags=["Auth"])
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 비밀번호를 변경합니다.
    changePassword(request.current_password, request.new_password, current_user, db)
    return ApiResponse()

@router.post("/change/nickname", response_model=ApiResponse, tags=["Auth"])
async def change_nickname(
    nickname_change_request: NicknameChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 닉네임을 변경합니다.
    await changeNickName(nickname_change_request.nickname, current_user, db)
    return ApiResponse()

@router.post("/change/mbti", response_model=ApiResponse, tags=["Auth"])
async def change_mbti(
    body: MbtiChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 사용자 정보를 수정합니다.
    await changeMbti(body.mbti, current_user, db)
    return ApiResponse()

@router.delete("/delete", response_model=ApiResponse, tags=["Auth"])
async def delete_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 사용자를 삭제합니다.
    await deleteUser(current_user, db)
    return ApiResponse()

@router.get("/kakao", response_model=ApiResponse, tags=["Auth"])
async def kakao():
    # 카카오 인증을 위한 URL을 반환합니다.
    return ApiResponse(data={"url": KAKAO_AUTH_URL})

@router.get("/kakao/test", response_model=ApiResponse, tags=["Auth"])
async def kakao_test():
    # 카카오 인증을 위한 URL을 반환합니다.
    return ApiResponse(data={"url": KAKAO_AUTH_URL_TEST})

@router.get("/kakao/callback", response_model=ApiResponse, tags=["Auth"])
async def kakao_callback(
        code: str,
        db: Session = Depends(get_db),
):
    # 카카오 로그인 콜백을 처리합니다.
    data = await get_user_kakao(code)
    user, is_sign_up = await user_kakao(data, db)
    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email) # 토큰을 생성합니다.
    return ApiResponse(
        success=True,
        data=KakaoTokenData(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="Bearer",
            is_signup=is_sign_up,
        )
    )

@router.get("/kakao/callback/test", response_model=ApiResponse, tags=["Auth"])
async def kakao_callback(
        code: str,
        db: Session = Depends(get_db),
):
    # 카카오 로그인 콜백을 처리합니다.
    data = await get_user_kakao_test(code)
    user, is_sign_up = await user_kakao(data, db)
    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email)  # 토큰을 생성합니다.
    return ApiResponse(
        success=True,
        data=KakaoTokenData(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="Bearer",
            is_signup=is_sign_up,
        )
    )

@router.post("/update", response_model=ApiResponse, tags=["Auth"])
async def update_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 사용자 정보를 수정합니다.
    await updateUser(request, current_user, db)
    return ApiResponse()

