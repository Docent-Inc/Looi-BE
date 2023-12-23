import random

import aioredis
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.Oauth import get_user_kakao, get_user_apple, check_user, get_user_line
from app.core.config import settings
from app.core.security import create_token, check_token, time_now
from app.db.database import get_db, save_db, get_redis_client
from app.db.models import User
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
                "local": f"https://appleid.apple.com/auth/authorize?client_id=looi.docent.zip&redirect_uri={settings.APPLE_REDIRECT_URI_DEV}&response_type=code%20id_token&scope=name%20email&response_mode=form_post",
                "dev": f"https://appleid.apple.com/auth/authorize?client_id=looi.docent.zip&redirect_uri={settings.APPLE_REDIRECT_URI_DEV}&response_type=code%20id_token&scope=name%20email&response_mode=form_post",
                "prod": f"https://appleid.apple.com/auth/authorize?client_id=looi.docent.zip&redirect_uri={settings.APPLE_REDIRECT_URI_PROD}&response_type=code%20id_token&scope=name%20email&response_mode=form_post"
            }
        }
        return AUTH_URLS[service][env]

    async def callback(self, service: str, env: str, code: str) -> TokenData:
        if service == "kakao":
            data = await get_user_kakao(code, env)
        elif service == "line":
            data = await get_user_line(code, env)
        elif service == "apple":
            data = await get_user_apple(code, env)
        user, is_sign_up = await check_user(data, self.db)
        expires_in, refresh_expires_in, access_token, refresh_token = await create_token(user.email)
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
        if user.is_sign_up == False:
            if auth_data.nickname != "":
                if self.db.query(User).filter(User.nickname == auth_data.nickname).first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=4008,
                    )
                user.nickname = auth_data.nickname
            if auth_data.mbti != "":
                user.mbti = auth_data.mbti
            if auth_data.gender != "":
                user.gender = auth_data.gender
            if auth_data.birth != "":
                user.birth = auth_data.birth
        elif user.is_sign_up == True:
            user.nickname = auth_data.nickname
            user.mbti = auth_data.mbti
            user.birth = auth_data.birth
            user.gender = auth_data.gender
            user.is_sign_up = False
        await self.redis.delete(f"user:{user.email}")
        save_db(user, self.db)

    async def update_push(self, auth_data: PushUpdateRequest, user: User) -> None:
        if auth_data.type == "morning":
            user.push_morning = auth_data.value
        elif auth_data.type == "night":
            user.push_night = auth_data.value
        elif auth_data.type == "report":
            user.push_report = auth_data.value
        await self.redis.delete(f"user:{user.email}")
        save_db(user, self.db)
    async def delete(self, user: User) -> None:
        user.is_deleted = True
        user.deleted_date = await time_now()
        await self.redis.delete(f"user:{user.email}")
        save_db(user, self.db)