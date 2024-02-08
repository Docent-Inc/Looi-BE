import asyncio
import random
from datetime import datetime

import aioredis
import firebase_admin
from fastapi import Depends
from firebase_admin import credentials
import json

from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session

from app.core.aiRequset import GPTService
from app.core.config import settings
from firebase_admin import messaging
from app.core.security import get_current_user, time_now
from app.db.database import get_redis_client, get_db, save_db
from app.db.models import User, Calendar, PushQuestion
from app.service.abstract import AbstractPushService
cred = credentials.Certificate(json.loads(settings.FIREBASE_JSON))
firebase_admin.initialize_app(cred)


class PushService(AbstractPushService):
    def __init__(self, db: Session = Depends(get_db), user: User = Depends(get_current_user), redis: aioredis.Redis = Depends(get_redis_client)):
        self.db = db
        self.user = user
        self.redis = redis

    async def test(self) -> None:
        push_question_list = [
            "오늘 아침에 눈을 떴을 때 기분이 어떠셨나요 🌅?",
            "오늘 하루 달성하고 싶은 목표가 있나요 🎯?",
            "오늘 가장 기대되는 일이 있으신가요 💡?",
            "오늘 새롭게 도전해보고 싶은 것이 있나요 🚀?",
            "아침을 시작하면서 듣고 싶은 노래가 있다면 무엇인가요 🎧? ",
        ]
        lock_key = "morning_push_lock"
        if await self.redis.set(lock_key, "locked", ex=60, nx=True):
            try:
                Users = self.db.query(User).filter(User.push_token != None, User.is_deleted == False,
                                                   User.push_morning == True).all()
                nickname_and_token = [(user.nickname, "dqS9j7Th50Rjh4txkuzgKu:APA91bGqAroOgppzD2I6rfvJ_MPLcPgArtad0cZBQQkzVtdrssOchf-HY4uFj9loPrVlSGrBYFxd4DKzuyHlvdZZi37d0rlMlPFU8G-TLQi7SCMvhkyWTfEIKPO4i_iiUXrRTnZuINud", user.device, random.choice(push_question_list))
                                      for user in Users]
                batch_size = 50
                for i in range(0, len(nickname_and_token), batch_size):
                    batch = nickname_and_token[i:i + batch_size]
                    tasks = [self.send(title="Looi", body=f"{nickname}님, {question}", token=token,
                                       landing_url=f"/chat?guide={nickname}님, {question}", device=f"{device}") for
                             nickname, token, device, question in batch]
                    await asyncio.gather(*tasks)
                    break

            finally:
                self.db.close()
                await self.redis.delete(lock_key)
                await self.redis.close()

    async def send(self, title: str, body: str, token: str, device: str, image_url: str = "", landing_url: str = "") -> None:
        try:
            # 데이터 필드 설정
            data = {}
            if landing_url:
                data["landing_url"] = landing_url
            if image_url:
                data["image_url"] = image_url

            data["title"] = title
            data["body"] = body

            if device == "iOS":
                notification = messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url if image_url else None,
                )
                apns_config = messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                        ),
                    )
                )
                message = messaging.Message(
                    notification=notification,
                    apns=apns_config,
                    token=token,
                    data=data,
                )
            if device == "AOS":
                android_config = messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default'
                    )
                )
                message = messaging.Message(
                    android=android_config,
                    token=token,
                    data=data,
                )

            # 비동기적으로 메시지 전송
            await asyncio.to_thread(messaging.send, message)
        except:
            pass


    async def send_morning_push(self) -> None:
        push_question_list = [
            "오늘 아침에 눈을 떴을 때 기분이 어떠셨나요 🌅?",
            "오늘 하루 달성하고 싶은 목표가 있나요 🎯?",
            "오늘 가장 기대되는 일이 있으신가요 💡?",
            "오늘 새롭게 도전해보고 싶은 것이 있나요 🚀?",
            "아침을 시작하면서 듣고 싶은 노래가 있다면 무엇인가요 🎧? ",
        ]
        lock_key = "morning_push_lock"
        if await self.redis.set(lock_key, "locked", ex=60, nx=True):
            try:
                Users = self.db.query(User).filter(User.push_token != None, User.is_deleted == False, User.push_morning == True).all()
                nickname_and_token = [(user.nickname, user.push_token, user.device, random.choice(push_question_list))
                                      for user in Users]
                batch_size = 50
                for i in range(0, len(nickname_and_token), batch_size):
                    batch = nickname_and_token[i:i + batch_size]
                    tasks = [self.send(title="Looi", body=f"{nickname}님, {question}", token=token,
                                       landing_url=f"/chat?guide={nickname}님, {question}", device=f"{device}") for
                             nickname, token, device, question in batch]
                    await asyncio.gather(*tasks)

            finally:
                self.db.close()
                await self.redis.delete(lock_key)
                await self.redis.close()


    async def send_afternoon_push(self) -> None:
        push_question_list = [
            "오늘 점심에 맛있는 거 드셨나요🍴?",
            "오전 중 가장 기억에 남는 순간이 있었나요? 저와 함께 그 순간을 되새겨봐요. 🕰️",
            "오늘 아침에 세운 목표 중 얼마나 달성했나요? 이야기해주세요. ✅",
            "점심 시간에 잘 쉬었나요? 잠깐의 휴식 동안 무슨 생각을 했는지 궁금해요. 🌿",
            "점심 시간에는 어떤 작은 행복을 느꼈나요? 간단한 순간이라도 공유해 주세요.🧘‍♂️",
        ]
        lock_key = "afternoon_push_lock"
        if await self.redis.set(lock_key, "locked", ex=60, nx=True):
            try:
                Users = self.db.query(User).filter(User.push_token != None, User.is_deleted == False,
                                                   User.push_morning == True).all()
                nickname_and_token = [(user.nickname, user.push_token, user.device, random.choice(push_question_list))
                                      for user in Users]
                batch_size = 50
                for i in range(0, len(nickname_and_token), batch_size):
                    batch = nickname_and_token[i:i + batch_size]
                    tasks = [self.send(title="Looi", body=f"{nickname}님, {question}", token=token,
                                       landing_url=f"/chat?guide={nickname}님, {question}", device=f"{device}") for
                             nickname, token, device, question in batch]
                    await asyncio.gather(*tasks)

            finally:
                self.db.close()
                await self.redis.delete(lock_key)
                await self.redis.close()

    async def send_night_push(self) -> None:
        lock_key = "night_push_lock"
        push_question_list = [
            "오늘 만난 사람들 중 인상 깊었던 사람이 있나요? 그사람이 어떤 영향을 미쳤는지 궁금해요.🌟",
            "오늘 있었던 일 중 내일 다시 해보고 싶은 일이 있나요? 🔄",
            "오늘 하루를 한 단어나 문장으로 표현한다면 어떨까요? ✨",
            "오늘 느낀 감정 중 가장 강렬했던 것은 무엇이었나요? 🔥",
            "만약 오늘을 다시 살 수 있다면, 무엇을 달리 하고 싶나요? 📆",
        ]

        default_question = random.choice(push_question_list)

        if await self.redis.set(lock_key, "locked", ex=60, nx=True):
            try:
                now = await time_now()
                Users = self.db.query(User).filter(User.push_token != None, User.is_deleted == False, User.push_night == True).all()
                nickname_and_token = [(user.nickname, user.push_token, user.id, user.device) for user in Users]

                batch_size = 50
                for i in range(0, len(nickname_and_token), batch_size):
                    batch = nickname_and_token[i:i + batch_size]
                    tasks = []
                    for nickname, token, user_id, device in batch:
                        # DB에서 해당 사용자의 오늘 생성된 질문 조회
                        question_record = self.db.query(PushQuestion).filter(
                            PushQuestion.User_id == user_id,
                            func.date(PushQuestion.create_date) == now.date()
                        ).first()

                        question = question_record.question if question_record else default_question
                        tasks.append(self.send(title="Looi", body=f"{nickname}님, {question}", token=token, landing_url=f"/chat?guide={nickname}님, {question}", device=f"{device}"))

                    await asyncio.gather(*tasks)
            finally:
                self.db.close()
                await self.redis.delete(lock_key)
                await self.redis.close()

    async def generate_night_push(self) -> None:
        lock_key = "generate_night_push_lock"
        if await self.redis.set(lock_key, "locked", ex=60, nx=True):
            try:
                now = await time_now()
                start_of_day = datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)
                eight_pm = start_of_day.replace(hour=20)

                Users = self.db.query(User).filter(User.push_token != None, User.is_deleted == False, User.push_night == True).all()

                user_calendar_data = {}
                for user in Users:
                    calendar_data = self.db.query(Calendar).filter(
                        Calendar.User_id == user.id,
                        Calendar.is_deleted == False,
                        Calendar.end_time > start_of_day,
                        Calendar.end_time < eight_pm,
                    ).order_by(Calendar.start_time).all()

                    if calendar_data:
                        # 마지막 일정 데이터 사용
                        text = f"[{user.nickname}], [{calendar_data[-1].title[:15]}], [{calendar_data[-1].content[:15]}]"
                        user_calendar_data[user.id] = text

                # 10개씩 나누어서 질문 생성
                batch_size = 10
                gpt_service = GPTService(db=self.db, user=user)
                user_calendar_data_keys = list(user_calendar_data.keys())  # 딕셔너리 키를 리스트로 변환
                for i in range(0, len(user_calendar_data_keys), batch_size):
                    batch_keys = user_calendar_data_keys[i:i + batch_size]  # 키 리스트 슬라이스
                    batch = {key: user_calendar_data[key] for key in batch_keys}  # 해당 키에 대한 딕셔너리 생성
                    tasks = [gpt_service.send_gpt_request(11, text) for text in batch.values()]
                    results = await asyncio.gather(*tasks)
                    # db에 저장
                    for user_id, result in zip(batch.keys(), results):
                        push_question = PushQuestion(
                            User_id=user_id,
                            calendar_content=batch[user_id][:255],
                            question=result[:255],
                            create_date=now,
                        )
                        save_db(push_question, self.db)
            finally:
                self.db.close()
                await self.redis.delete(lock_key)
                await self.redis.close()

    async def push_schedule(self) -> None:
        lock_key = "push_schedule_lock"
        if await self.redis.set(lock_key, "locked", ex=60, nx=True):
            try:
                now = await time_now()
                push_calendar_list = self.db.query(Calendar).filter(
                    func.date(Calendar.push_time) == now.date(),
                    func.hour(Calendar.push_time) == now.hour,
                    func.minute(Calendar.push_time) == now.minute
                ).all()

                user_calendar_data = []
                for calendar in push_calendar_list:
                    user = self.db.query(User).filter(User.id == calendar.User_id).first()
                    date_str = datetime.strftime(calendar.start_time, "%Y-%m-%d")
                    landing_url = f"/mypage?tab=calendar&date={date_str}"
                    # 알림 메시지 생성
                    if user.push_schedule == 0:
                        body = f"{user.nickname}님, {calendar.title}가 지금 시작합니다. 일정을 위해 준비해 주세요 ⏰"
                    elif user.push_schedule in [5, 10, 15, 30]:
                        body = f"{user.nickname}님, {calendar.title}까지 {user.push_schedule}분 남았습니다. 일정을 위해 준비해 주세요 ⏰"
                    elif user.push_schedule in [60, 120, 180]:
                        body = f"{user.nickname}님, {calendar.title}까지 {user.push_schedule // 60}시간 남았습니다. 일정을 위해 준비해 주세요 ⏰"
                    user_calendar_data.append((user.nickname, user.push_token, body, landing_url, user.device))

                batch_size = 50  # 배치 사이즈 설정
                for i in range(0, len(user_calendar_data), batch_size):
                    batch = user_calendar_data[i:i + batch_size]
                    tasks = []
                    for nickname, token, body, landing_url, device in batch:
                        tasks.append(self.send(title="Looi", body=body, token=token, landing_url=landing_url, device=f"{device}"))
                    await asyncio.gather(*tasks)

            finally:
                self.db.close()
                await self.redis.delete(lock_key)
                await self.redis.close()
