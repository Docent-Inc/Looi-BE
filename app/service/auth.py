import random
from datetime import datetime, timedelta

import aioredis
from fastapi import Depends, Cookie, Response
from sqlalchemy.orm import Session

from app.core.Oauth import get_user_kakao, get_user_apple, check_user, get_user_line
from app.core.config import settings
from app.core.security import create_token, check_token, time_now
from app.db.database import get_db, save_db, get_redis_client
from app.db.models import User, NightDiary, Calendar
from app.schemas.request import UserUpdateRequest, PushUpdateRequest
from app.schemas.response import TokenData
from app.service.abstract import AbstractAuthService

class AuthService(AbstractAuthService):
    def __init__(self, db: Session = Depends(get_db), redis: aioredis.Redis = Depends(get_redis_client)):
        self.db = db
        self.redis = redis

    async def login(self, service: str, env: str) -> str:
        AUTH_URLS = {
            "kakao": {
                "local": f"https://kauth.kakao.com/oauth/authorize?client_id={settings.KAKAO_API_KEY}&redirect_uri={settings.KAKAO_REDIRECT_URI_LOCAL}&response_type=code",
                "dev": f"https://kauth.kakao.com/oauth/authorize?client_id={settings.KAKAO_API_KEY}&redirect_uri={settings.KAKAO_REDIRECT_URI_DEV}&response_type=code",
                "prod": f"https://kauth.kakao.com/oauth/authorize?client_id={settings.KAKAO_API_KEY}&redirect_uri={settings.KAKAO_REDIRECT_URI_PROD}&response_type=code"
            },
            "line": {
                "local": f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={settings.LINE_CHANNEL_ID}&redirect_uri={settings.LINE_REDIRECT_URI_LOCAL}&state={random.randint(1000000000, 9999999999)}&scope=profile%20openid%20email",
                "dev": f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={settings.LINE_CHANNEL_ID}&redirect_uri={settings.LINE_REDIRECT_URI_DEV}&state={random.randint(1000000000, 9999999999)}&scope=profile%20openid%20email",
                "prod": f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={settings.LINE_CHANNEL_ID}&redirect_uri={settings.LINE_REDIRECT_URI_PROD}&state={random.randint(1000000000, 9999999999)}&scope=profile%20openid%20email"
            },
            "apple": {
                "local": f"https://appleid.apple.com/auth/authorize?client_id=looi.docent.zip&redirect_uri={settings.APPLE_REDIRECT_URI_DEV}&response_type=code&response_mode=query",
                "dev": f"https://appleid.apple.com/auth/authorize?client_id=looi.docent.zip&redirect_uri={settings.APPLE_REDIRECT_URI_DEV}&response_type=code&response_mode=query",
                "prod": f"https://appleid.apple.com/auth/authorize?client_id=looi.docent.zip&redirect_uri={settings.APPLE_REDIRECT_URI_PROD}&response_type=code&response_mode=query"
            }
        }
        return AUTH_URLS[service][env]

    async def callback(self, service: str, env: str, code: str, response: Response) -> TokenData:
        if service == "kakao":
            data = await get_user_kakao(code, env)
        elif service == "line":
            data = await get_user_line(code, env)
        elif service == "apple":
            data = await get_user_apple(code, env)
        user, is_sign_up = await check_user(data, service, self.db)
        expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email)
        # 쿠키에 액세스 토큰과 리프레시 토큰 설정
        # response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=expires_in)
        # response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=refresh_expires_in)
        return TokenData(
                user_name=user.nickname,
                access_token=access_token,
                expires_in=expires_in,
                refresh_token=refresh_token,
                refresh_expires_in=refresh_expires_in,
                token_type="Bearer",
                is_signup=is_sign_up,
        )

    async def refresh(self, refresh_token: str) -> TokenData:
        user = await check_token(refresh_token, self.db)
        expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email)
        return TokenData(
                user_name=user.nickname,
                access_token=access_token,
                expires_in=expires_in,
                refresh_token=refresh_token,
                refresh_expires_in=refresh_expires_in,
                token_type="bearer",
                is_signup=False,
            )

    async def info(self, user: User) -> User:
        user.hashed_password = None
        return user

    async def update(self, auth_data: UserUpdateRequest, user: User) -> None:
        if auth_data.nickname != "":
            user.nickname = auth_data.nickname
        if auth_data.mbti != "":
            user.mbti = auth_data.mbti
        if auth_data.gender != "":
            user.gender = auth_data.gender
            night_diary = self.db.query(NightDiary).filter(NightDiary.User_id == user.id).first()
            if user.gender == "남":
                night_diary.image_url = "https://kr.object.ncloudstorage.com/looi/onboarding_male.png"
            else:
                night_diary.image_url = "https://kr.object.ncloudstorage.com/looi/onboarding_female.png"
            save_db(night_diary, self.db)
        if auth_data.birth != "":
            user.birth = auth_data.birth
        if auth_data.push_token != "":
            user.push_token = auth_data.push_token
        if auth_data.device != "":
            user.device = auth_data.device

        user.is_sign_up = False
        await self.redis.delete(f"user:{user.email}")
        save_db(user, self.db)

    async def update_push(self, auth_data: PushUpdateRequest, user: User) -> None:
        if auth_data.type == "morning":
            user.push_morning = auth_data.value
        elif auth_data.type == "night":
            user.push_night = auth_data.value
        elif auth_data.type == "schedule":
            user.push_schedule = auth_data.value

            calendar_list = self.db.query(Calendar).filter(
                Calendar.start_time > await time_now(),
                Calendar.User_id == user.id
            ).all()

            for calendar in calendar_list:
                push_time_delta = timedelta(minutes=user.push_schedule)
                push_time = datetime.strptime(str(calendar.start_time), '%Y-%m-%d %H:%M:%S') - push_time_delta
                calendar.push_time = push_time
                save_db(calendar, self.db)


        await self.redis.delete(f"user:{user.email}")
        save_db(user, self.db)
    async def delete(self, user: User) -> None:
        user.is_deleted = True
        user.deleted_date = await time_now()
        await self.redis.delete(f"user:{user.email}")
        save_db(user, self.db)