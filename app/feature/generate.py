from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import extcolors
from app.core.config import settings
from app.core.security import time_now
from app.db.database import get_redis_client, save_db
from app.db.models import MorningDiary, NightDiary, Calendar, Report, Luck, Prompt

from app.feature.aiRequset import GPTService
from app.schemas.response import User

async def generate_luck(user: User, db: Session):
    today = await time_now()
    text = ""
    morning = db.query(MorningDiary).filter(
                MorningDiary.User_id == user.id,
                MorningDiary.create_date >= today.date() - timedelta(days=1),
                MorningDiary.is_deleted == False
            ).first()
    if not morning:
        text = "x"
    else:
        if morning:
            text = morning.content
    gpt_service = GPTService(user, db)
    data = await gpt_service.send_gpt_request(4, text)
    luck = Luck(
        User_id=user.id,
        text=text,
        content=data,
        create_date=today.date(),
    )
    save_db(luck, db)
    return data