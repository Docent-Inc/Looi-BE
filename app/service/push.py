import asyncio
import aioredis
import firebase_admin
from fastapi import Depends
from firebase_admin import credentials
import json
from sqlalchemy.orm import Session
from app.core.config import settings
from firebase_admin import messaging
from app.core.security import get_current_user
from app.db.database import get_redis_client, get_db
from app.db.models import User
from app.service.abstract import AbstractPushService
cred = credentials.Certificate(json.loads(settings.FIREBASE_JSON))
firebase_admin.initialize_app(cred)


class PushService(AbstractPushService):
    def __init__(self, db: Session = Depends(get_db), user: User = Depends(get_current_user), redis: aioredis.Redis = Depends(get_redis_client)):
        self.db = db
        self.user = user
        self.redis = redis

    async def test(self, title: str, body: str, landing_url: str, image_url: str, token: str) -> None:
        await self.send(title=title, body=body, token=token, image_url=image_url, landing_url=landing_url)

    async def send(self, title: str, body: str, token: str, image_url: str = "", landing_url: str = "") -> None:
        try:
            # 이미지 URL이 비어있지 않은 경우에만 포함
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url if image_url else None,
            )

            # 데이터 필드 설정
            data = {}
            if landing_url:
                data["landing_url"] = landing_url

            # 메시지 구성
            message = messaging.Message(
                notification=notification,
                token=token,
                data=data,
            )

            # 비동기적으로 메시지 전송
            await asyncio.to_thread(messaging.send, message)
        except Exception as e:
            print(e)

    async def send_all(self, title: str, body: str) -> None:
        # 토큰 리스트와 닉네임 추출
        Users = self.db.query(User).filter(User.push_token != None, User.is_deleted == False).all()
        nickname_and_token = [(user.nickname, user.push_token) for user in Users]

        # 100개씩 토큰을 나누어 배치 전송
        batch_size = 100
        for i in range(0, len(nickname_and_token), batch_size):
            batch = nickname_and_token[i:i + batch_size]

            tasks = [self.send(title=title, body=f"{nickname}{body}", token=token) for nickname, token in batch]
            await asyncio.gather(*tasks)

    async def send_morning_push(self) -> None:
        lock_key = "morning_push_lock"
        if await self.redis.set(lock_key, "locked", ex=300, nx=True):
            try:
                await self.send_all("Looi", "님, 오늘은 어떤 꿈을 꾸셨나요?")
            finally:
                self.db.close()
                await self.redis.delete(lock_key)

    async def send_night_push(self) -> None:
        lock_key = "night_push_lock"
        if await self.redis.set(lock_key, "locked", ex=300, nx=True):
            try:
                await self.send_all("Looi", "님, 오늘은 어떤 하루를 보내셨나요?")
            finally:
                self.db.close()
                await self.redis.delete(lock_key)