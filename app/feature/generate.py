from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import extcolors
from app.core.config import settings
from app.core.security import time_now
from app.db.database import get_redis_client, save_db
from app.db.models import MorningDiary, NightDiary, Calendar, Report, Luck, Prompt
from io import BytesIO
import asyncio
import requests
from PIL import Image
import json

from app.feature.aiRequset import GPTService
from app.schemas.response import User

async def image_background_color(image_url: str):
    response = await asyncio.to_thread(requests.get, image_url)
    img = Image.open(BytesIO(response.content))
    width, height = img.size

    # 이미지를 상하로 2등분
    upper_half = img.crop((0, 0, width, height // 2))
    lower_half = img.crop((0, height // 2, width, height))

    # 각 부분의 대표색 추출
    upper_colors, _ = extcolors.extract_from_image(upper_half)
    lower_colors, _ = extcolors.extract_from_image(lower_half)

    upper_dominant_color = upper_colors[0][0]
    lower_dominant_color = lower_colors[0][0]

    return upper_dominant_color, lower_dominant_color

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