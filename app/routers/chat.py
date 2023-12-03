import aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import random
from app.core.config import settings
from app.core.security import get_current_user, text_length, time_now
from app.db.database import get_db, get_redis_client
from app.db.models import WelcomeChat, HelperChat, Chat
from app.feature.chat import classify_text
from app.schemas.request import ChatRequest
from app.schemas.response import ApiResponse, User, ChatResponse

router = APIRouter(prefix="/chat")

@router.post("", tags=["Chat"])
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client),
) -> ApiResponse:

    # 택스트 길이 확인
    text = await text_length(body.content, settings.MAX_LENGTH)

    # 하루 요청 제한 확인
    now = await time_now()
    chat_count_key = f"chat_count:{current_user.id}:{now.day}"
    current_count = await redis.get(chat_count_key) or 0
    if int(current_count) > settings.MAX_CALL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4404
        )

    # 텍스트 분류 및 저장
    diary_id, content, text_type = await classify_text(body.type, text, current_user, db)

    # 채팅 카운트 증가
    await redis.set(chat_count_key, int(current_count) + 1, ex=86400)  # 하루 동안 유효한 카운트

    # 응답
    return ApiResponse(
        data=ChatResponse(
            calls_left=settings.MAX_CALL - int(current_count) - 1,
            text_type=text_type,
            diary_id=diary_id,
            content=content
        )
    )

@router.get("/welcome", tags=["Chat"])
async def get_welcome(
    type: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:

    # type에 맞는 채팅방 인사 문구 가져오기
    data = db.query(WelcomeChat).filter(WelcomeChat.is_deleted == False, WelcomeChat.type == type).all()

    # 랜덤으로 하나 선택
    random_chat = random.choice(data)
    random_chat.text = random_chat.text.replace("{}", current_user.nickname)

    # 응답
    return ApiResponse(
        data=random_chat
    )

@router.get("/helper", tags=["Chat"])
async def get_helper(
    type: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:

    # type에 맞는 채팅 도움말 가져오기
    data = db.query(HelperChat).filter(HelperChat.is_deleted == False, HelperChat.type == type).all()

    # 랜덤으로 하나 선택
    random_chat = random.choice(data)

    # 응답
    return ApiResponse(
        data=random_chat
    )


# @router.get("/list", tags=["Chat"])
# async def generate_chat_list(
#     page: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ) -> ApiResponse:
#     chat = db.query(Chat).filter(Chat.User_id == current_user.id, Chat.is_deleted == False).order_by(Chat.id.desc()).offset((page-1) * 10).limit(10).all()
#     total_counts = db.query(Chat).filter(Chat.User_id == current_user.id, Chat.is_deleted == False).count()
#     return ApiResponse(
#         data={
#             "page_num": page,
#             "total_counts": total_counts,
#             "list": chat
#     })