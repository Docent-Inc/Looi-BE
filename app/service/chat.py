import random

import aioredis
from fastapi import Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user, time_now, check_length
from app.db.database import get_db, get_redis_client, save_db
from app.db.models import User, TextClassification, WelcomeChat, HelperChat
from app.core.aiRequset import GPTService
from app.schemas.request import ChatRequest, CreateCalendarRequest, CreateDreamRequest, CreateDiaryRequest, \
    CreateMemoRequest
from app.schemas.response import ChatResponse
from app.service.abstract import AbstractChatService
from app.service.calendar import CalendarService
from app.service.diary import DiaryService
from app.service.dream import DreamService
from app.service.memo import MemoService


class ChatService(AbstractChatService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db),
                 redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def create(self, chat_data: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
        # 택스트 길이 확인
        await check_length(chat_data.content, settings.MAX_LENGTH, 4221)

        # 하루 요청 제한 확인
        now = await time_now()
        chat_count_key = f"chat_count:{self.user.id}:{now.day}"
        current_count = await self.redis.get(chat_count_key) or 0
        if int(current_count) > settings.MAX_CALL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4404
            )

        # 텍스트 분류
        gpt_service = GPTService(self.user, self.db)
        if chat_data.type == 0:
            try:
                # 텍스트 분류 시도
                number = await gpt_service.send_gpt_request(1, chat_data.content[:200])
                chat_data.type = int(number.strip())
            except:
                # 텍스트 분류 실패
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4013
                )

        # 텍스트 저장
        text_type_dict = {1: "꿈", 2: "일기", 3: "메모", 4: "일정"}
        save_chat = TextClassification(
            text=chat_data.content,
            User_id=self.user.id,
            text_type=text_type_dict[chat_data.type],
            create_date=await time_now(),
        )
        save_db(save_chat, self.db)

        # type별 작업
        if chat_data.type == 1:
            dream_service = DreamService(self.user, self.db, self.redis)
            diary = await dream_service.create(CreateDreamRequest(content=chat_data.content))
        elif chat_data.type == 2:
            diary_service = DiaryService(self.user, self.db, self.redis)
            diary = await diary_service.create(CreateDiaryRequest(content=chat_data.content), background_tasks)
        elif chat_data.type == 3:
            memo_service = MemoService(self.user, self.db, self.redis)
            diary = await memo_service.create(CreateMemoRequest(content=chat_data.content))
        elif chat_data.type == 4:
            calendar_service = CalendarService(self.user, self.db, self.redis)
            diary = await calendar_service.create(CreateCalendarRequest(content=chat_data.content))
        else:
            # 텍스트 분류 실패
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4013
            )

        # 채팅 카운트 증가
        await self.redis.set(chat_count_key, int(current_count) + 1, ex=86400)  # 하루 동안 유효한 카운트

        return ChatResponse(
            calls_left=settings.MAX_CALL - int(current_count) - 1,
            text_type=chat_data.type,
            diary_id=diary.id,
            content=diary
        )

    async def welcome(self, text_type: int) -> object:
        # type에 맞는 채팅방 인사 문구 가져오기
        data = self.db.query(WelcomeChat).filter(WelcomeChat.is_deleted == False, WelcomeChat.type == text_type).all()

        # 랜덤으로 하나 선택
        random_chat = random.choice(data)

        return {"text": random_chat.text.replace("{}", self.user.nickname)}

    async def helper(self, text_type: int) -> object:
        # type에 맞는 채팅 도움말 가져오기
        data = self.db.query(HelperChat).filter(HelperChat.is_deleted == False, HelperChat.type == text_type).all()
        # 랜덤으로 하나 선택
        random_chat = random.choice(data)

        return random_chat