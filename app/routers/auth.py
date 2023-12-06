from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.feature.kakaoOAuth2 import KAKAO_AUTH_URL, get_user_kakao, KAKAO_AUTH_URL_TEST, \
    get_user_kakao_test, KAKAO_AUTH_URL_VERCEL, get_user_kakao_vercel
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import decode_access_token, create_token, get_update_user
from app.feature.lineOAuth2 import LINE_AUTH_URL, LINE_AUTH_URL_TEST, get_user_line, get_user_line_test
from app.schemas.response import TokenData, ApiResponse, KakaoTokenData
from app.schemas.request import TokenRefresh, UserUpdateRequest, PushUpdateRequest
from app.feature.user import get_user_by_email, changeNickName, \
    deleteUser, user_kakao, changeMbti, updateUser, updatePush, user_line
from app.schemas.request import NicknameChangeRequest, \
    MbtiChangeRequest
from app.core.security import get_current_user
from app.schemas.response import User
router = APIRouter(prefix="/auth")

@router.get("/login/{service}", response_model=ApiResponse, tags=["Auth"])
async def login(
    service: str,
    test: Optional[bool] = False
):
    if service == "kakao":
        return ApiResponse(data={"url": KAKAO_AUTH_URL_TEST if test else KAKAO_AUTH_URL})
    elif service == "line":
        return ApiResponse(data={"url": LINE_AUTH_URL_TEST if test else LINE_AUTH_URL})
    elif service == "vercel":
        return ApiResponse(data={"url": KAKAO_AUTH_URL_VERCEL})

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=4403)

@router.get("/callback/{service}", response_model=ApiResponse, tags=["Auth"])
async def callback(
    service: str,
    code: str,
    db: Session = Depends(get_db),
):
    # 콜백을 처리합니다.
    if service == "kakao":
        data = await get_user_kakao_test(code) if test else await get_user_kakao(code)
        user, is_sign_up = await user_kakao(data, db)
    elif service == "line":
        data = await get_user_line_test(code) if test else await get_user_line(code)
        user, is_sign_up = await user_line(data, db)
    elif service == "vercel":
        data = await get_user_kakao_vercel(code)
        user, is_sign_up = await user_kakao(data, db)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=4403)

    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email)
    return ApiResponse(
        success=True,
        data=KakaoTokenData(
            user_name=user.nickname,
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="Bearer",
            is_signup=is_sign_up,
        )
    )

@router.post("/refresh", response_model=ApiResponse, tags=["Auth"])
async def refresh_token(
    token_refresh: TokenRefresh,
    db: Session = Depends(get_db),
):
    payload = await decode_access_token(token_refresh.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4004,
        )
    email: str = payload.get("sub")
    user = await get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4005,
        )
    if user.is_sign_up == True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4998,
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

@router.get("/info", response_model=ApiResponse, tags=["Auth"])
async def get_info(
    current_user: User = Depends(get_current_user),
):
    current_user.hashed_password = None
    return ApiResponse(data=current_user)

@router.post("/update", response_model=ApiResponse, tags=["Auth"])
async def update_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_update_user),
    db: Session = Depends(get_db),
):
    await updateUser(request, current_user, db)
    return ApiResponse()


@router.post("/update/nickname", response_model=ApiResponse, tags=["Auth"])
async def change_nickname(
    nickname_change_request: NicknameChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await changeNickName(nickname_change_request.nickname, current_user, db)
    return ApiResponse()

@router.post("/update/mbti", response_model=ApiResponse, tags=["Auth"])
async def change_mbti(
    body: MbtiChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await changeMbti(body.mbti, current_user, db)
    return ApiResponse()

@router.post("/update/push", response_model=ApiResponse, tags=["Auth"])
async def update_push(
    request: PushUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await updatePush(request, current_user, db)
    return ApiResponse()

@router.delete("/delete", response_model=ApiResponse, tags=["Auth"])
async def delete_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await deleteUser(current_user, db)
    return ApiResponse()



