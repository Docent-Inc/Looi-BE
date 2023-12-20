import datetime
import json
from datetime import timedelta
from random import randint

import aioredis
from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.aiRequset import GPTService
from app.core.security import get_current_user, time_now
from app.db.database import get_db, get_redis_client, save_db
from app.db.models import User, MorningDiary, Luck, NightDiary, Calendar
from app.service.abstract import AbstractTodayService


class TodayService(AbstractTodayService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db),
                 redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def luck(self) -> dict:
        now = await time_now()
        cached_luck = self.db.query(Luck).filter(
            Luck.User_id == self.user.id,
            Luck.create_date == now.date(),
            Luck.is_deleted == False
        ).first()

        if cached_luck:
            return {"luck": cached_luck.content, "isCheckedToday": True}

        text = ""
        morning = self.db.query(MorningDiary).filter(
            MorningDiary.User_id == self.user.id,
            MorningDiary.create_date >= now.date() - timedelta(days=1),
            MorningDiary.is_deleted == False
        ).first()
        if not morning:
            text = "x"
        else:
            if morning:
                text = morning.content
        gpt_service = GPTService(self.user, self.db)
        data = await gpt_service.send_gpt_request(4, text)
        luck = Luck(
            User_id=self.user.id,
            text=text,
            content=data,
            create_date=now.date(),
        )
        save_db(luck, self.db)

        return {"luck": luck.content, "isCheckedToday": False}

    async def history(self) -> dict:
        now = await time_now()
        cached_data_json = await self.redis.get(f"history:{self.user.id}:{now.day}")

        if cached_data_json:
            cached_data = json.loads(cached_data_json)
            return cached_data

        n = randint(1, 2)
        if n == 1:
            count_morning = 1
            count_night = 2
        else:
            count_morning = 2
            count_night = 1

        random_morning_diaries = self.db.query(MorningDiary).filter(
            MorningDiary.is_deleted == False,
            MorningDiary.User_id == self.user.id
        ).order_by(func.random()).limit(count_morning).all()
        random_night_diaries = self.db.query(NightDiary).filter(
            NightDiary.is_deleted == False,
            NightDiary.User_id == self.user.id
        ).order_by(func.random()).limit(count_night).all()

        def diary_to_dict(diary):
            # 날짜-시간 필드를 문자열로 변환
            diary_dict = diary.as_dict()
            if diary_dict.get("create_date"):
                diary_dict["create_date"] = diary_dict["create_date"].strftime("%Y-%m-%d %H:%M:%S")
            if diary_dict.get("modify_date"):
                diary_dict["modify_date"] = diary_dict["modify_date"].strftime("%Y-%m-%d %H:%M:%S")
            return diary_dict

        data = {
            "MorningDiary": [{"diary_type": 1, **diary_to_dict(diary)} for diary in random_morning_diaries],
            "NightDiary": [{"diary_type": 2, **diary_to_dict(diary)} for diary in random_night_diaries]
        }


        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        seconds_until_midnight = (midnight - now).total_seconds()
        await self.redis.set(f"history:{self.user.id}:{now.day}", json.dumps(data), ex=int(seconds_until_midnight))

        return data

    async def calendar(self) -> object:
        today = await time_now()
        upcoming_events = self.db.query(Calendar).filter(
            Calendar.User_id == self.user.id,
            Calendar.start_time >= today,
            Calendar.is_deleted == False
        ).order_by(Calendar.start_time).limit(5).all()
        return upcoming_events