import json
from datetime import datetime
from random import randint

import aioredis
import pytz
import redis as redis
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.apiDetail import ApiDetail
from app.core.security import get_current_user, time_now
from app.db.database import get_db, get_redis_client
from app.db.models import Calender, MorningDiary, NightDiary, Report, Luck
from app.feature.generate import generate_luck
from app.schemas.response import User, ApiResponse

router = APIRouter(prefix="/today")

@router.get("/calender", tags=["Today"])
async def get_calender(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    today = await time_now()
    upcoming_events = db.query(Calender).filter(
        Calender.User_id == current_user.id,
        Calender.start_time >= today,
        Calender.is_deleted == False
    ).order_by(Calender.start_time).limit(5).all()
    return ApiResponse(
        data=upcoming_events
    )
get_calender.__doc__ = f"[API detail]({ApiDetail.get_calender})"

def default_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

@router.get("/history", tags=["Today"])
async def get_record(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        redis: aioredis.Redis = Depends(get_redis_client),
) -> ApiResponse:
    now = await time_now()
    today_str = now.strftime('%Y-%m-%d')
    redis_key = f"history:{today_str}:user_{current_user.id}"

    cached_data_json = await redis.get(redis_key)

    if cached_data_json:
        cached_data = json.loads(cached_data_json)
        return ApiResponse(data=cached_data)

    n = randint(1, 2)
    if n == 1:
        count_morning = 1
        count_night = 2
    else:
        count_morning = 2
        count_night = 1

    random_morning_diaries = db.query(MorningDiary).filter(
        MorningDiary.is_deleted == False,
        MorningDiary.User_id == current_user.id
    ).order_by(func.random()).limit(count_morning).all()
    random_night_diaries = db.query(NightDiary).filter(
        NightDiary.is_deleted == False,
        NightDiary.User_id == current_user.id
    ).order_by(func.random()).limit(count_night).all()

    data = {
        "MorningDiary": [diary.as_dict() for diary in random_morning_diaries],
        "NightDiary": [diary.as_dict() for diary in random_night_diaries]
    }

    ttl = (now.replace(hour=23, minute=59, second=59) - now).seconds
    data_json = json.dumps(data, default=default_converter)
    await redis.setex(redis_key, ttl, data_json)

    return ApiResponse(data=data)
get_record.__doc__ = f"[API detail]({ApiDetail.get_record})"

@router.get("/luck", tags=["Today"])
async def luck(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    now = await time_now()
    cached_luck = db.query(Luck).filter(
        Luck.User_id == current_user.id,
        Luck.create_date == now.date(),
        Luck.is_deleted == False
    ).first()

    if cached_luck:
        return ApiResponse(data={"luck": cached_luck.content, "isCheckedToday": True})

    luck_content = await generate_luck(current_user, db)
    return ApiResponse(data={"luck": luck_content,  "isCheckedToday": False})
luck.__doc__ = f"[API detail]({ApiDetail.generate_luck})"