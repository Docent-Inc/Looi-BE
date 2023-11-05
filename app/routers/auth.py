from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.apiDetail import ApiDetail
from app.feature.kakaoOAuth2 import KAKAO_AUTH_URL, get_user_kakao, KAKAO_AUTH_URL_TEST, \
    get_user_kakao_test
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import decode_access_token, create_token
from app.feature.lineOAuth2 import LINE_AUTH_URL, LINE_AUTH_URL_TEST, get_user_line, get_user_line_test
from app.feature.slackBot import slack_bot
from app.schemas.response import TokenData, ApiResponse, KakaoTokenData
from app.schemas.request import TokenRefresh, UserUpdateRequest, PushUpdateRequest
from app.feature.user import get_user_by_email, create_user, authenticate_user, changeNickName, changePassword, \
    deleteUser, user_kakao, changeMbti, updateUser, updatePush, user_line
from app.schemas.request import UserCreate, PasswordChangeRequest, NicknameChangeRequest, \
    MbtiChangeRequest
from app.core.security import get_current_user
from app.schemas.response import User

router = APIRouter(prefix="/auth")

# @router.post("/signup", response_model=ApiResponse, tags=["Auth"])
# async def signup(
#     user_data: UserCreate, # UserCreate 스키마를 사용합니다.
#     db: Session = Depends(get_db), # 데이터베이스 세션을 받아옵니다.
# ):
#     existing_user = get_user_by_email(db, email=user_data.email) # 이메일로 사용자를 조회합니다.
#     if existing_user: # 사용자가 존재하면
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=4001,
#         )
#     existing_user = get_user_by_nickname(db, nickname=user_data.nickname) # 닉네임으로 사용자를 조회합니다.
#     if existing_user:  # 사용자가 존재하면
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=4002,
#         )
#     new_user = await create_user(db, user_data) # 사용자를 생성합니다.
#     expires_in, refresh_expires_in, access_token, refresh_token = await create_token(new_user.email) # 토큰을 생성합니다.
#     return ApiResponse(
#         data=TokenData(
#             access_token=access_token,
#             expires_in=expires_in,
#             refresh_token=refresh_token,
#             refresh_expires_in=refresh_expires_in,
#             token_type="bearer",
#         ),
#     )

# @router.post("/login", response_model=ApiResponse, tags=["Auth"])
# async def login(
#     form_data: OAuth2PasswordRequestForm = Depends(), # OAuth2PasswordRequestForm을 사용합니다.
#     db: Session = Depends(get_db),
# ):
#     user = authenticate_user( # 이메일과 비밀번호로 사용자를 조회합니다.
#         db, email=form_data.username, password=form_data.password
#     )
#     if not user: # 사용자가 존재하지 않으면
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=4003,
#         )
#     expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email) # 토큰을 생성합니다.
#     return ApiResponse(
#         data=TokenData(
#             access_token=access_token,
#             expires_in=expires_in,
#             refresh_token=refresh_token,
#             refresh_expires_in=refresh_expires_in,
#             token_type="Bearer",
#         )
#     )
# @router.post("/update/password", response_model=ApiResponse, tags=["Auth"])
# async def change_password(
#     request: PasswordChangeRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     changePassword(request.current_password, request.new_password, current_user, db)
#     return ApiResponse()

@router.get("/login/{service}", response_model=ApiResponse, tags=["Auth"])
async def login(
    service: str,
    test: Optional[bool] = False
):
    if service == "kakao":
        return ApiResponse(data={"url": KAKAO_AUTH_URL_TEST if test else KAKAO_AUTH_URL})
    elif service == "line":
        return ApiResponse(data={"url": LINE_AUTH_URL_TEST if test else LINE_AUTH_URL})
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=4403)
login.__doc__ = f"[API detail]({ApiDetail.login})"

@router.get("/callback/{service}", response_model=ApiResponse, tags=["Auth"])
async def callback(
    service: str,
    code: str,
    db: Session = Depends(get_db),
    test: Optional[bool] = False
):
    # 콜백을 처리합니다.
    if service == "kakao":
        data = await get_user_kakao_test(code) if test else await get_user_kakao(code)
        user, is_sign_up = await user_kakao(data, db)
    elif service == "line":
        data = await get_user_line_test(code) if test else await get_user_line(code)
        user, is_sign_up = await user_line(data, db)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=4403)

    expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email)
    await slack_bot(f"회원가입: {user.nickname}({user.email})")
    return ApiResponse(
        success=True,
        data=TokenData(
            user_name=user.nickname,
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            token_type="Bearer",
            is_signup=is_sign_up,
        )
    )
callback.__doc__ = f"[API detail]({ApiDetail.callback})"

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
    user = get_user_by_email(db, email=email)
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
refresh_token.__doc__ = f"[API detail]({ApiDetail.refresh_token})"

@router.get("/info", response_model=ApiResponse, tags=["Auth"])
async def get_info(
    current_user: User = Depends(get_current_user),
):
    current_user.hashed_password = None
    return ApiResponse(data=current_user)
get_info.__doc__ = f"[API detail]({ApiDetail.get_info})"

@router.post("/update", response_model=ApiResponse, tags=["Auth"])
async def update_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await updateUser(request, current_user, db)
    return ApiResponse()
update_user.__doc__ = f"[API detail]({ApiDetail.update_user})"


@router.post("/update/nickname", response_model=ApiResponse, tags=["Auth"])
async def change_nickname(
    nickname_change_request: NicknameChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await changeNickName(nickname_change_request.nickname, current_user, db)
    return ApiResponse()
change_nickname.__doc__ = f"[API detail]({ApiDetail.change_nickname})"

@router.post("/update/mbti", response_model=ApiResponse, tags=["Auth"])
async def change_mbti(
    body: MbtiChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await changeMbti(body.mbti, current_user, db)
    return ApiResponse()
change_mbti.__doc__ = f"[API detail]({ApiDetail.change_mbti})"

@router.post("/update/push", response_model=ApiResponse, tags=["Auth"])
async def update_push(
    request: PushUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await updatePush(request, current_user, db)
    return ApiResponse()
update_push.__doc__ = f"[API detail]({ApiDetail.update_push})"

@router.delete("/delete", response_model=ApiResponse, tags=["Auth"])
async def delete_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await deleteUser(current_user, db)
    return ApiResponse()
delete_user.__doc__ = f"[API detail]({ApiDetail.delete_user})"



