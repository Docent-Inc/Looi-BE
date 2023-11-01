

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import random
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import MorningDiary, NightDiary, Memo, Calender, WelcomeChat, HelperChat, Chat
from app.feature.aiRequset import send_gpt4_request
from app.feature.diary import create_morning_diary, create_night_diary, create_memo
from app.feature.generate import generate_schedule
from app.schemas.request import ChatRequest
from app.schemas.response import ApiResponse, User

router = APIRouter(prefix="/chat")

@router.post("", tags=["Chat"])
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    사용자의 택스트를 4가지 카테고리로 분류합니다.
    '''
    try:
        text = body.content
        number = await send_gpt4_request(1, text)
        text_type = int(number.strip())
        if text_type == 1:
            diary_id = await create_morning_diary(body.content, current_user, db)
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
    return ApiResponse(
        data={
            "text_type": text_type,
            "diary_id": diary_id,
            "content": content
        }
    )

@router.get("/list", tags=["Generate"])
async def generate_chat_list(
    page: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    # db에서 사용자의 채팅 리스트를 가져옵니다.
    chat = db.query(Chat).filter(Chat.User_id == current_user.id, Chat.is_deleted == False).order_by(Chat.id.desc()).offset((page-1) * 10).limit(10).all()
    total_counts = db.query(Chat).filter(Chat.User_id == current_user.id, Chat.is_deleted == False).count()
    return ApiResponse(
        data={
            "page_num": page,
            "total_counts": total_counts,
            "list": chat
    })

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

@router.get("/helper", tags=["Chat"])
async def get_tip(
    type: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    data = db.query(HelperChat).filter(HelperChat.is_deleted == False, HelperChat.type == type).all()
    random_chat = random.choice(data)
    return ApiResponse(
        data=random_chat
    )