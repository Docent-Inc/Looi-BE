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

    async def test(self) -> None:
        await self.send("test", "test", self.user.push_token)

    async def send(self, title: str, body: str, token: str) -> None:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        messaging.send(message)
