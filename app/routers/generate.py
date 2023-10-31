from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status

from app.db.models import Chat, MorningDiary, Calender, Memo, NightDiary
from app.feature.aiRequset import send_gpt_request, send_gpt4_request
from app.feature.diary import create_morning_diary, create_night_diary, create_memo, create_calender
from app.feature.generate import generate_image, generate_schedule, generate_report, generate_luck
from app.core.security import get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session
import random

from app.schemas.request import ChatRequest
from app.schemas.response import ApiResponse, User

router = APIRouter(prefix="/generate")

@router.get("/chat/list", tags=["Generate"])
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

@router.get("/report", tags=["Generate"])
async def report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    # db에서 최근 7일간의 MorningDiary, NightDiary, Calendar를 불러옵니다
    report = await generate_report(current_user, db)
    # 그리고 그것을 바탕으로 사용자의 리포트를 생성합니다.
    return ApiResponse(
        data=report
    )

@router.get("/luck", tags=["Generate"])
async def luck(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    luck = await generate_luck(current_user, db)
    return ApiResponse(
        data={"luck": luck}
    )