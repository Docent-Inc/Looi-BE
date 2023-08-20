import asyncio
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status
from app.db.models import NightDiary, MorningDiary
from app.feature.generate import generate_image, generate_diary_name, generate_resolution_clova
import datetime
import pytz
from app.schemas.response import User

async def create_morning_diary(image_model: int, content: str, user: User, db: Session) -> int:
    # 그림과 일기의 제목과 해몽을 생성합니다.
    mbti_content = content if user.mbti is None else user.mbti + ", " + content

    image_url, diary_name, resolution = await asyncio.gather(
        generate_image(image_model, content),
        generate_diary_name(content),
        generate_resolution_clova(mbti_content)
    )
    diary = MorningDiary(
        content=content,
        User_id=user.id,
        image_url=image_url,
        diary_name=diary_name,
        resolution=resolution,
        create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
        modify_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
    )
    try:
        db.add(diary)
        db.commit()
        db.refresh(diary)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,  # 에러 메시지를 반환합니다.
        )
    return diary.id

async def read_morning_diary(diary_id: int, user:User, db: Session) -> MorningDiary:
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.User_id == user.id).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )
    return diary

async def create_night_diary(image_model: int, content: str, user: User, db: Session) -> int:
    # 그림과 일기의 제목을 생성합니다.
    image_url, diary_name = await asyncio.gather(
        generate_image(image_model, content),
        generate_diary_name(content)
    )

    # 저녁 일기를 생성합니다.
    diary = NightDiary(
        content=content,
        User_id=user.id,
        image_url=image_url,
        diary_name=diary_name,
        create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
        modify_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
    )
    try:
        db.add(diary)
        db.commit()
        db.refresh(diary)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )
    return diary.id

async def read_night_diary(diary_id: int, user:User, db: Session) -> NightDiary:
    diary = db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == user.id).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4012,
        )
    return diary