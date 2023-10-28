import json
from datetime import datetime, timedelta
from random import random

import pytz
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Calender, MorningDiary, NightDiary, Report
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

@router.get("/report", tags=["Today"])
async def get_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    # db에서 가장 최근의 마음 보고서를 가져옵니다.
    report = db.query(Report).filter(
        Report.User_id == current_user.id,
        Report.is_deleted == False
    ).order_by(Report.create_date.desc()).first()
    return ApiResponse(
        data={"create_date": report.create_date, "content": json.loads(report.content)}
    )

@router.get("/history", tags=["Today"])
async def get_record(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    # db에서 지금까지 만들어진 이미지를 랜덤으로 3개 가져옵니다.
    random_morning_diaries = db.query(MorningDiary).filter(MorningDiary.is_deleted == False, MorningDiary.User_id == current_user.id).order_by(func.random()).limit(2).all()
    random_night_diaries = db.query(NightDiary).filter(NightDiary.is_deleted == False, NightDiary.User_id == current_user.id).order_by(func.random()).limit(2).all()

    data = {
        "MoringDiary": [diary.as_dict() for diary in random_morning_diaries],
        "NightDiary": [diary.as_dict() for diary in random_night_diaries]
    }
    return ApiResponse(
        data=data
    )
