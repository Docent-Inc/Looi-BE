from datetime import datetime, timedelta

import aioredis
import pytz
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import extcolors
from app.core.config import settings
from app.core.security import time_now
from app.db.database import get_redis_client
from app.db.models import MorningDiary, NightDiary, Calender, Report, Luck, Chat, Prompt
from app.feature.aiRequset import send_gpt_request, send_dalle2_request, send_gpt4_request
import uuid
from io import BytesIO
import asyncio
import requests
from PIL import Image
from google.cloud import storage
from google.oauth2 import service_account
import json
from app.schemas.response import User
SERVICE_ACCOUNT_INFO = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)

async def generate_resolution_gpt(text: str, user: User, db: Session, redis_key: str) -> str:
    dream_resolution = await send_gpt4_request(2, text, user, db)
    redis_client = await get_redis_client()
    diary_id = await redis_client.get(redis_key)
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id).first()
    diary.resolution = dream_resolution
    db.commit()
    db.refresh(diary)
    return dream_resolution
async def generate_diary_name(message: str, user: User, db: Session) -> str:
    dreamName = await send_gpt_request(2, message, user, db)
    return dreamName
async def generate_image(image_model: int, message: str, user: User, db: Session):
    prompt = await send_gpt_request(3, message, user, db)

    if image_model == 1:
        dream_image_url = await send_dalle2_request(prompt, user, db)

    save_promt = Prompt(
        text=message,
        prompt=prompt,
    )
    db.add(save_promt)
    db.commit()
    db.refresh(save_promt)

    try:
        response = await asyncio.to_thread(requests.get, dream_image_url)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4500
        )
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

    unique_id = uuid.uuid4()
    destination_blob_name = str(unique_id) + ".png"
    bucket_name = "docent"  # 구글 클라우드 버킷 이름
    credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
    client = storage.Client(credentials=credentials, project=SERVICE_ACCOUNT_INFO['project_id'])

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    with BytesIO(buffer.getvalue()) as image_file:
        image_file.seek(0)
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(image_file)
        blob.make_public()

    return [blob.public_url, upper_dominant_color, lower_dominant_color]

async def generate_schedule(text: str, user: User, db: Session) -> str:
    schedule = await send_gpt_request(4, text, user, db)
    try:
        calender = Calender(
            User_id=user.id,
            title=schedule['title'],
            start_time=schedule['start_time'],
            end_time=schedule['end_time'],
            content=schedule['description'],
            create_date=await time_now(),
        )
        db.add(calender)
        db.commit()

        chat = Chat(
            User_id=user.id,
            content=text,
            create_date=datetime.now(pytz.timezone('Asia/Seoul')),
            is_chatbot=False,
            is_deleted=False
        )
        db.add(chat)
        db.commit()

        chat = Chat(
            User_id=user.id,
            content_type=4,
            Calender_id=calender.id,
            content=schedule['title'],
            event_time=schedule['start_time'],
            is_chatbot=True,
            create_date=datetime.now(pytz.timezone('Asia/Seoul')),
            is_deleted=False
        )
        db.add(chat)
        db.commit()

        return calender.id
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4014
        )

async def generate_luck(user: User, db: Session):
    today = await time_now()
    text = ""
    morning = db.query(MorningDiary).filter(
                MorningDiary.User_id == user.id,
                MorningDiary.create_date >= today.date() - timedelta(days=1),
                MorningDiary.is_deleted == False
            ).first()
    if not morning:
        text = ""
    else:
        if morning:
            text += morning.content
    data = await send_gpt_request(5, text, user, db)
    luck = Luck(
        User_id=user.id,
        content=data,
        create_date=today.date()
    )
    db.add(luck)
    db.commit()
    return data