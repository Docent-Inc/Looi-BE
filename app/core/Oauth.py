import datetime

import jwt
import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_user_by_email, get_password_hash, time_now
from app.db.database import save_db
from app.db.models import User, NightDiary


async def get_user_kakao(code: str, env: str) -> dict:
    if env == "local":
        REDIRECT_URI = settings.KAKAO_REDIRECT_URI_LOCAL
    elif env == "dev":
        REDIRECT_URI = settings.KAKAO_REDIRECT_URI_DEV
    elif env == "prod":
        REDIRECT_URI = settings.KAKAO_REDIRECT_URI_PROD
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_API_KEY,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        response = requests.post("https://kauth.kakao.com/oauth/token", data=data)
        token = response.json().get("access_token")

        headers = {"Authorization": f"Bearer {token}"}
        user_info = requests.get("https://kapi.kakao.com/v2/user/me", headers=headers).json()

        user_id = user_info["id"]
        user_email = user_info["kakao_account"]["email"]
        return {"user_id": user_id, "email": user_email}
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4010,
        )

async def get_user_line(code: str, env: str) -> dict:
    if env == "local":
        REDIRECT_URI = settings.LINE_REDIRECT_URI_LOCAL
    elif env == "dev":
        REDIRECT_URI = settings.LINE_REDIRECT_URI_DEV
    elif env == "prod":
        REDIRECT_URI = settings.LINE_REDIRECT_URI_PROD
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.LINE_CHANNEL_ID,
            "client_secret": settings.LINE_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        response = requests.get("https://api.line.me/oauth2/v2.1/token", data=data)
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        user_info = requests.get("https://api.line.me/v2/profile", headers=headers).json()
        # TODO: user_info format 확인
        user_id = user_info["userId"]
        user_email = user_info["email"]
        return {"user_id": user_id, "email": user_email}
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4010,
        )

async def get_user_apple(code: str, env: str) -> dict:
    if env == "dev":
        REDIRECT_URI = settings.APPLE_REDIRECT_URI_DEV
    elif env == "prod":
        REDIRECT_URI = settings.APPLE_REDIRECT_URI_PROD

    private_key = settings.APPLE_LOGIN_KEY
    headers = {
        'kid': '9SSBB74MBU'
    }

    payload = {
        'iss': '76KPWSL348',
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        'aud': 'https://appleid.apple.com',
        'sub': 'looi.docent.zip',
    }

    client_secret = jwt.encode(
        payload,
        private_key,
        algorithm='ES256',
        headers=headers
    )

    if env == "dev":
        REDIRECT_URI = settings.APPLE_REDIRECT_URI_DEV
    elif env == "prod":
        REDIRECT_URI = settings.APPLE_REDIRECT_URI_PROD
    try:
        # Prepare data for the token request
        data = {
            "grant_type": "authorization_code",
            "client_id": "looi.docent.zip",
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        # Make the token request
        response = requests.post("https://appleid.apple.com/auth/token", data=data)
        id_token = response.json().get("id_token")
        unverified_claims = jwt.decode(id_token, options={"verify_signature": False}, audience="looi.docent.zip")
        user_id = unverified_claims.get('sub')
        email = unverified_claims.get('email')
        return {"user_id": user_id, "email": email}
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4024,
        )

async def check_user(data: dict, db: Session):
    try:
        user_id = str(data["user_id"])
        user_email = data["email"]
        user_nickname = user_id.split("@")[0]
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=4024,
        )
    user = await get_user_by_email(db, email=user_email)
    is_sign_up = False
    if not user:
        now = await time_now()
        user = User(
            email=user_email,
            nickname=user_nickname,
            hashed_password=get_password_hash(user_id),
            gender="0",
            age_range="0",
            image_model=1,
            language_id=1,
            mbti="0",
            Oauth_from="apple",
            create_date=now,
        )
        is_sign_up = True
        user = save_db(user, db)
        diary = NightDiary(
            User_id=user.id,
            diary_name="나만의 기록 친구 Look-i와의 특별한 첫 만남",
            content="오늘은 인상깊은 날이다. 기록 친구 Look-i와 만나게 되었다. 앞으로 기록 열심히 해야지~!",
            image_url="https://storage.googleapis.com/docent/c1c96c92-a8d2-4b18-9465-48be554d8880.png",
            background_color="[\"(253, 254, 253)\", \"(77, 37, 143)\"]",
            create_date=now,
            modify_date=now,
        )
        save_db(diary, db)
    if user.mbti == "0":
        is_sign_up = True
    return user, is_sign_up