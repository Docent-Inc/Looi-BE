from datetime import datetime, timedelta

import pytz
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Calender, MorningDiary, NightDiary
from app.schemas.response import User, ApiResponse

router = APIRouter(prefix="/today")

@router.get("/calender", tags=["Today"])
async def get_calender(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    # db에서 사용자의 오늘의 일정을 가져옵니다.
    today = datetime.now(pytz.timezone('Asia/Seoul'))
    calender = db.query(Calender).filter(
        Calender.User_id == current_user.id,
        Calender.start_time >= today.date(),
        Calender.start_time < today.date() + timedelta(days=1),
        Calender.is_deleted == False
    ).all()
    return ApiResponse(
        data=calender
    )

@router.get("/record", tags=["Today"])
async def get_record(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
     # db에서 오늘 사용자의 기록을 가져옵니다.
    today = datetime.now(pytz.timezone('Asia/Seoul'))
    # Morning
    morning = db.query(MorningDiary).filter(
        MorningDiary.User_id == current_user.id,
        MorningDiary.create_date >= today.date(),
        MorningDiary.create_date < today.date() + timedelta(days=1),
        MorningDiary.is_deleted == False
    ).first()
    night = db.query(NightDiary).filter(
        NightDiary.User_id == current_user.id,
        NightDiary.create_date >= today.date(),
        NightDiary.create_date < today.date() + timedelta(days=1),
        NightDiary.is_deleted == False
    ).first()
    return ApiResponse(
        data={
            "morning": morning,
            "night": night
        }
    )