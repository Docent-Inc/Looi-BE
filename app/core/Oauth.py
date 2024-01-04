import datetime
import uuid

import jwt
import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, time_now
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
        email = str(user_id[:6]) + "@privaterelay.appleid.com"
        return {"user_id": user_id, "email": email}
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4024,
        )

async def check_user(data: dict, service: str, db: Session):
    try:
        user_id = str(data["user_id"])
        user_email = data["email"]
        user_nickname = user_email.split("@")[0]
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=4024,
        )
    user = db.query(User).filter(User.email == user_email, User.is_deleted == False).first()
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
            Oauth_from=service,
            create_date=now,
            last_active_date=now,
        )
        is_sign_up = True
        user = save_db(user, db)
        diary = NightDiary(
            User_id=user.id,
            diary_name="나만의 기록 친구 Looi와의 특별한 첫 만남",
            content="오늘은 인상깊은 날이다. 기록 친구 Looi와 만나게 되었다. 앞으로 기록 열심히 해야지~!",
            resolution="오늘 같은 특별한 날이 기억에 오래 남을 수 있도록 만들어주는 멋진 친구 Looi와 만남이 있었군요! 이런 만남은 삶에 긍정적인 변화를 가져다주고, 새로운 습관이나 좋은 결심을 시작하는데 도움을 줍니다. 앞으로 기록을 열심히 하기로 한 결심을 실천하여, 일상의 소중함과 성장의 순간들을 남겨두시면 좋겠네요. 지금의 생각과 감정, 목표와 꿈들을 기록하는 것은 추후에 돌이켜보았을 때 살아온 길을 반추하고 다시 동기부여를 얻는 데 큰 힘이 될 것입니다. 오늘의 만남이 앞으로 여러분의 기록 여정에 큰 영감을 주길 바라며, 새로운 습관을 잘 유지하시길 응원합니다!",
            image_url="https://kr.object.ncloudstorage.com/looi/onboarding_female.png",
            main_keyword="[\"기록의 습관\", \"Looi와의 만남\", \"새로운 시작\", \"Look at yourself\"]",
            share_id=str(uuid.uuid4()),
            is_generated=True,
            create_date=now,
            modify_date=now,
        )
        save_db(diary, db)
    if user.mbti == "0":
        is_sign_up = True
    return user, is_sign_up