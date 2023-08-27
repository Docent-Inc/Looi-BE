import asyncio
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status
from app.db.models import NightDiary, MorningDiary, Memo, Calender
from app.feature.generate import generate_image, generate_diary_name, generate_resolution_clova
import datetime
import pytz

from app.schemas.request import UpdateDiaryRequest, CalenderRequest
from app.schemas.response import User

async def create_morning_diary(content: str, user: User, db: Session) -> int:
    # 그림과 일기의 제목과 해몽을 생성합니다.
    mbti_content = content if user.mbti is None else user.mbti + ", " + content

    L, diary_name, resolution = await asyncio.gather(
        generate_image(user.image_model, content),
        generate_diary_name(content),
        generate_resolution_clova(mbti_content)
    )
    diary = MorningDiary(
        content=content,
        User_id=user.id,
        image_url=L[0],
        background_color=L[1],
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
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.User_id == user.id, MorningDiary.is_deleted == False).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )
    return diary

async def update_morning_diary(diary_id: int, content: UpdateDiaryRequest, user: User, db: Session) -> int:
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.User_id == user.id, MorningDiary.is_deleted == False).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )
    try:
        diary.diary_name = content.diary_name
        diary.content = content.diary_content
        diary.modify_date = datetime.datetime.now(pytz.timezone('Asia/Seoul'))
        db.commit()
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )
    return diary_id

async def delete_morning_diary(diary_id: int, user: User, db: Session):
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.User_id == user.id, MorningDiary.is_deleted == False).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )
    try:
        diary.is_deleted = True
        db.commit()
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )
async def list_morning_diary(page: int, user: User, db: Session):
    diaries = db.query(MorningDiary).filter(MorningDiary.User_id == user.id, MorningDiary.is_deleted == False).order_by(MorningDiary.create_date.desc()).limit(5).offset((page-1)*5).all()
    return diaries

async def create_night_diary(content: str, user: User, db: Session):
    # 그림과 일기의 제목을 생성합니다.
    L, diary_name = await asyncio.gather(
        generate_image(user.image_model, content),
        generate_diary_name(content)
    )

    # 저녁 일기를 생성합니다.
    diary = NightDiary(
        content=content,
        User_id=user.id,
        image_url=L[0],
        background_color=L[1],
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
    diary = db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == user.id, NightDiary.is_deleted == False).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4012,
        )
    return diary

async def update_night_diary(diary_id: int, content: UpdateDiaryRequest, user: User, db: Session) -> int:
    diary = db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == user.id, NightDiary.is_deleted == False).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4012,
        )
    try:
        diary.diary_name = content.diary_name
        diary.content = content.diary_content
        diary.modify_date = datetime.datetime.now(pytz.timezone('Asia/Seoul'))
        db.commit()
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )
    return diary.id

async def delete_night_diary(diary_id: int, user: User, db: Session) -> int:
    diary = db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == user.id, NightDiary.is_deleted == False).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4012,
        )
    try:
        diary.is_deleted = True
        db.commit()
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )

async def list_night_diary(page: int, user: User, db: Session):
    diaries = db.query(NightDiary).filter(NightDiary.User_id == user.id, NightDiary.is_deleted == False).order_by(NightDiary.create_date.desc()).limit(5).offset((page-1)*5).all()
    return diaries
async def create_memo(content: str, user: User, db: Session) -> int:
    # TODO: 메모의 제목과 카테고리를 생성합니다.
    # 메모를 생성합니다.
    memo = Memo(
        content=content,
        User_id=user.id,
        create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
        modify_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
    )
    try:
        db.add(memo)
        db.commit()
        db.refresh(memo)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )
    return memo.id

async def read_memo(memo_id: int, user: User, db: Session) -> Memo:
    memo = db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == user.id, Memo.is_deleted == False).first()
    if not memo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4016,
        )
    return memo

async def create_calender(body: CalenderRequest, user: User, db: Session) -> int:
    calender = Calender(
        User_id=user.id,
        start_date=body.start_date,
        end_date=body.end_date,
        title=body.title,
        content=body.content,
    )
    try:
        db.add(calender)
        db.commit()
        db.refresh(calender)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )
    return calender.id

async def read_calender(calender_id: int, user: User, db: Session) -> Calender:
    calender = db.query(Calender).filter(Calender.id == calender_id, Calender.User_id == user.id, Calender.is_deleted == False).first()
    if not calender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4015,
        )
    return calender

async def update_calender(calender_id: int, body: CalenderRequest, user: User, db: Session) -> int:
    calender = db.query(Calender).filter(Calender.id == calender_id, Calender.User_id == user.id, Calender.is_deleted == False).first()
    if not calender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4015,
        )
    try:
        calender.start_date = body.start_date
        calender.end_date = body.end_date
        calender.title = body.title
        calender.content = body.content
        db.commit()
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )
    return calender.id

async def delete_calender(calender_id: int, user: User, db: Session):
    calender = db.query(Calender).filter(Calender.id == calender_id, Calender.User_id == user.id, Calender.is_deleted == False).first()
    if not calender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4015,
        )
    try:
        calender.is_deleted = True
        db.commit()
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )

async def list_calender(user: User, db: Session):
    calenders = db.query(Calender).filter(Calender.User_id == user.id, Calender.is_deleted == False).all()
    return calenders