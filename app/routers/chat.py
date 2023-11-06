import aioredis
import redis as redis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
import random

from app.core.apiDetail import ApiDetail
from app.core.config import settings
from app.core.security import get_current_user, text_length, time_now
from app.db.database import get_db, get_redis_client
from app.db.models import MorningDiary, NightDiary, Memo, Calender, WelcomeChat, HelperChat, Chat, TextClassification
from app.feature.aiRequset import send_gpt4_request
from app.feature.diary import create_morning_diary, create_night_diary, create_memo
from app.feature.generate import generate_schedule
from app.schemas.request import ChatRequest
from app.schemas.response import ApiResponse, User

router = APIRouter(prefix="/chat")

@router.post("", tags=["Chat"])
async def chat(
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client),
) -> ApiResponse:
    text = await text_length(body.content, settings.MAX_LENGTH)
    now = await time_now()
    chat_count_key = f"chat_count:{current_user.id}:{now.day}"
    total_count_key = f"chat_count:total"
    total_count = await redis.get(total_count_key) or 0
    current_count = await redis.get(chat_count_key) or 0
    if int(current_count) > settings.MAX_CALL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4404
        )
    try:
        number = await send_gpt4_request(1, text, current_user, db)
        text_type = int(number.strip())
        text_type_dict = {1: "꿈", 2: "일기", 3: "메모", 4: "일정"}
        save_chat = TextClassification(
            text=body.content,
            text_type=text_type_dict[text_type],
            create_date=await time_now(),
        )
        db.add(save_chat)
        db.commit()
        db.refresh(save_chat)
        if text_type == 1:
            diary_id = await create_morning_diary(body.content, current_user, db, background_tasks)
            content = db.query(MorningDiary).filter(MorningDiary.id == diary_id).first()
        elif text_type == 2:
            diary_id = await create_night_diary(body.content, current_user, db)
            content = db.query(NightDiary).filter(NightDiary.id == diary_id).first()
        elif text_type == 3:
            diary_id = await create_memo(body.content, current_user, db)
            content = db.query(Memo).filter(Memo.id == diary_id).first()
        elif text_type == 4:
            diary_id = await generate_schedule(body.content, current_user, db)
            content = db.query(Calender).filter(Calender.id == diary_id).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4013
            )
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4013
        )
    await redis.set(chat_count_key, int(current_count) + 1, ex=86400)  # 하루 동안 유효한 카운트
    await redis.set(total_count_key, int(total_count) + 1, ex=86400)  # 하루 동안 유효한 카운트
    return ApiResponse(
        data={
            "calls_left": settings.MAX_CALL - int(current_count) - 1,
            "text_type": text_type,
            "diary_id": diary_id,
            "content": content
        }
    )
chat.__doc__ = f"[API detail]({ApiDetail.chat})"

@router.get("/list", tags=["Chat"])
async def generate_chat_list(
    page: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    chat = db.query(Chat).filter(Chat.User_id == current_user.id, Chat.is_deleted == False).order_by(Chat.id.desc()).offset((page-1) * 10).limit(10).all()
    total_counts = db.query(Chat).filter(Chat.User_id == current_user.id, Chat.is_deleted == False).count()
    return ApiResponse(
        data={
            "page_num": page,
            "total_counts": total_counts,
            "list": chat
    })
generate_chat_list.__doc__ = f"[API detail]({ApiDetail.generate_chat_list})"

@router.get("/welcome", tags=["Chat"])
async def get_welcome(
    type: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    data = db.query(WelcomeChat).filter(WelcomeChat.is_deleted == False, WelcomeChat.type == type).all()
    random_chat = random.choice(data)
    random_chat.text = random_chat.text.replace("{}", current_user.nickname)
    return ApiResponse(
        data=random_chat
    )
get_welcome.__doc__ = f"[API detail]({ApiDetail.get_welcome})"

@router.get("/helper", tags=["Chat"])
async def get_helper(
    type: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    data = db.query(HelperChat).filter(HelperChat.is_deleted == False, HelperChat.type == type).all()
    random_chat = random.choice(data)
    return ApiResponse(
        data=random_chat
    )
get_helper.__doc__ = f"[API detail]({ApiDetail.get_helper})"