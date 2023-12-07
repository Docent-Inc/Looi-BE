from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash, time_now
from app.schemas.request import UserCreate, UserUpdateRequest, PushUpdateRequest
from typing import Optional
from app.core.security import get_user_by_email, get_user_by_nickname
from app.db.models import User, NightDiary
import requests
from fastapi import HTTPException, status
from httpx_oauth.errors import GetIdEmailError
from app.core.config import settings
import random

CLIENT_ID = settings.KAKAO_API_KEY
CLIENT_SECRET = settings.KAKAO_CLIENT_SECRET
REDIRECT_URI = "https://docent.zip/callback"
REDIRECT_URI_TEST = "http://localhost:3000/callback"
REDIRECT_URI_DEV = "https://bmongsmong.com/callback"
KAKAO_AUTH_URL_TEST = f"https://kauth.kakao.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI_TEST}&response_type=code"
KAKAO_AUTH_URL = f"https://kauth.kakao.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
KAKAO_AUTH_URL_DEV = f"https://kauth.kakao.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI_DEV}&response_type=code"
AUTHORIZE_ENDPOINT = "https://kauth.kakao.com/oauth/authorize"
ACCESS_TOKEN_ENDPOINT = "https://kauth.kakao.com/oauth/token"
PROFILE_ENDPOINT_KAKAO = "https://kapi.kakao.com/v2/user/me"
BASE_SCOPES = ["account_email"]
BASE_PROFILE_SCOPES = ["kakao_account.email"]
LINE_CHANNEL_ID = settings.LINE_CHANNEL_ID
LINE_SECRET = settings.LINE_SECRET
PROFILE_ENDPOINT_LINE = "https://api.line.me/v2/profile"
REDIRECT_URI_TEST = "http://localhost:3000/line"
LINE_AUTH_URL = f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={LINE_CHANNEL_ID}&redirect_uri={REDIRECT_URI}&state={random.randint(1000000000, 9999999999)}&scope=profile%20openid%20email"
LINE_AUTH_URL_TEST = f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={LINE_CHANNEL_ID}&redirect_uri={REDIRECT_URI_TEST}&state={random.randint(1000000000, 9999999999)}&scope=profile%20openid%20email"



mbti_list = ['istj', 'isfj', 'infj', 'intj', 'istp', 'isfp', 'infp', 'intp', 'estp', 'esfp', 'enfp', 'entp', 'estj', 'esfj', 'enfj', 'entj']

async def get_user_kakao(request: str, env: str):
    global REDIRECT_URI
    if env == "local":
        REDIRECT_URI = REDIRECT_URI_TEST
    elif env == "dev":
        REDIRECT_URI = REDIRECT_URI_DEV
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code": request,
        }
        response = requests.post(ACCESS_TOKEN_ENDPOINT, data=data)
        token = response.json().get("access_token")

        headers = {"Authorization": f"Bearer {token}"}
        user_info = requests.get(PROFILE_ENDPOINT_KAKAO, headers=headers).json()
        return user_info
    except GetIdEmailError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4010,
        )

async def get_user_line(request: str, env: str):
    global REDIRECT_URI
    if env == "local":
        REDIRECT_URI = REDIRECT_URI_TEST
    elif env == "dev":
        REDIRECT_URI = REDIRECT_URI_DEV
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": LINE_CHANNEL_ID,
            "client_secret": LINE_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": request,
        }
        response = requests.get("https://api.line.me/oauth2/v2.1/token", data=data)

        token = response.json().get("access_token")
        print(token)

        # headers = {"Authorization": f"Bearer {token}"}
        # user_info = requests.get(PROFILE_ENDPOINT_LINE, headers=headers).json()
        # return user_info
    except GetIdEmailError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4010,
        )

async def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        nickname=user.nickname,
        email=user.email,
        hashed_password=hashed_password,
        image_model=1,
        is_deleted=False,
        create_date=await time_now(),
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,  # 에러 메시지를 반환합니다.
        )

# def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
#     user = get_user_by_email(db, email) # 이메일로 사용자 정보 가져오기
#     if not user:
#         return None
#     if not verify_password(password, user.hashed_password): # 비밀번호 확인
#         return None
#     return user

async def changeNickName(requset_nickName: str, current_user: User, db: Session):
    existing_user = await get_user_by_nickname(db, nickname=requset_nickName)  # 닉네임으로 사용자를 조회합니다.
    if existing_user:  # 사용자가 존재하면
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4008,  # 에러 메시지를 반환합니다.
        )
    # 닉네임을 변경합니다.
    try:
        current_user.nickname = requset_nickName
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,  # 에러 메시지를 반환합니다.
        )


def changePassword(request_password: str, new_password: str, current_user: User, db: Session):
    # 증명되지 않은 사용자는 비밀번호를 변경할 수 없습니다.
    if not verify_password(request_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4006,
        )
    # 새로운 비밀번호를 해시합니다.
    if verify_password(new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4007,
        )
    current_user.hashed_password = get_password_hash(new_password)
    try:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )

async def changeMbti(mbti: str, user: User, db: Session):
    # mbti가 유효한지 확인합니다.
    if mbti not in mbti_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4009,
        )
    # mbti를 변경합니다.
    try:
        user.mbti = mbti
        db.add(user)
        db.commit()
        db.refresh(user)
    except:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )

async def updatePush(request: PushUpdateRequest, current_user: User, db: Session):
    if request.type =="morning":
        current_user.push_morning = request.value
    elif request.type =="night":
        current_user.push_night = request.value
    elif request.type =="report":
        current_user.push_report = request.value
    db.add(current_user)
    db.commit()

async def deleteUser(current_user: User, db: Session):
    # 사용자의 삭제 상태를 변경합니다.
    current_user.is_deleted = True
    current_user.deleted_date = await time_now()
    try:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )

async def user_kakao(kakao_data: dict, db: Session) -> Optional[User]:
    # 카카오에서 전달받은 사용자 정보를 변수에 저장합니다.
    try:
        kakao_id = str(kakao_data["id"])
        kakao_email = kakao_data["kakao_account"]["email"]
        kakao_nickname = kakao_email.split("@")[0]
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=4010,
        )
    try:
        gender = kakao_data["kakao_account"]["gender"]
    except:
        gender = "0"
    try:
        age_range = kakao_data["kakao_account"]["age_range"]
    except:
        age_range = "0"

    # 카카오에서 전달받은 사용자 정보로 사용자를 조회합니다.
    user = await get_user_by_email(db, email=kakao_email)
    is_sign_up = False
    # 사용자가 존재하지 않으면 새로운 사용자를 생성합니다.
    if not user:
        user = User(
            email=kakao_email,
            nickname=kakao_nickname,
            hashed_password=get_password_hash(kakao_id),
            gender=str(gender),
            age_range=str(age_range),
            image_model=1,
            language_id=1,
            mbti=str(0),
            Oauth_from="kakao",
            create_date=await time_now(),
        )
        is_sign_up = True
        try:
            now = await time_now()
            db.add(user)
            db.commit()
            db.refresh(user)
            diary = NightDiary(
                User_id=user.id,
                diary_name="나만의 기록 친구 Look-i와의 특별한 첫 만남",
                content="오늘은 인상깊은 날이다. 기록 친구 Look-i와 만나게 되었다. 앞으로 기록 열심히 해야지~!",
                image_url="https://storage.googleapis.com/docent/c1c96c92-a8d2-4b18-9465-48be554d8880.png",
                background_color="[\"(253, 254, 253)\", \"(77, 37, 143)\"]",
                create_date=now,
                modify_date=now,
            )
            db.add(diary)
            db.commit()
            db.refresh(diary)
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=5000,
            )
    if user.mbti == "0":
        is_sign_up = True
    return user, is_sign_up

async def user_line(kakao_data: dict, db: Session) -> Optional[User]:
    # TODO : line 로그인 구현
    try:
        kakao_id = str(kakao_data["id"])
        kakao_email = kakao_data["kakao_account"]["email"]
        kakao_nickname = kakao_email.split("@")[0]
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=4010,
        )
    try:
        gender = kakao_data["kakao_account"]["gender"]
    except:
        gender = "0"
    try:
        age_range = kakao_data["kakao_account"]["age_range"]
    except:
        age_range = "0"

    # 카카오에서 전달받은 사용자 정보로 사용자를 조회합니다.
    user = await get_user_by_email(db, email=kakao_email)
    is_sign_up = False
    # 사용자가 존재하지 않으면 새로운 사용자를 생성합니다.
    if not user:
        user = User(
            email=kakao_email,
            nickname=kakao_nickname,
            hashed_password=get_password_hash(kakao_id),
            gender=str(gender),
            age_range=str(age_range),
            image_model=1,
            language_id=1,
            mbti=str(0),
            Oauth_from="line",
            create_date=await time_now(),
        )
        is_sign_up = True
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=5000,
            )
    if user.mbti == "0":
        is_sign_up = True
    return user, is_sign_up

async def updateUser(request: UserUpdateRequest, current_user: User, db: Session):
    try:
        current_user.nickname = request.nickname
        current_user.mbti = request.mbti
        current_user.gender = request.gender
        current_user.birth = request.birth
        current_user.is_sign_up = False
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )