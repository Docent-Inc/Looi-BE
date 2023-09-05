import asyncio
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status
from app.db.models import NightDiary, MorningDiary, Memo, Calender, Chat
from app.feature.aiRequset import send_gpt_request
from app.feature.generate import generate_image, generate_diary_name, generate_resolution_gpt
import datetime
import pytz

from app.schemas.request import UpdateDiaryRequest, CalenderRequest, ListRequest
from app.schemas.response import User

async def create_morning_diary(content: str, user: User, db: Session) -> int:
    try:
        chat = Chat(
            User_id=user.id,
            is_chatbot=False,
            create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
            content=content,
        )
        db.add(chat)
        db.commit()
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,  # 에러 메시지를 반환합니다.
        )
    # 그림과 일기의 제목과 해몽을 생성합니다.
    mbti_content = content if user.mbti is None else user.mbti + ", " + content

    L, diary_name, resolution = await asyncio.gather(
        generate_image(user.image_model, content),
        generate_diary_name(content),
        generate_resolution_gpt(mbti_content)
    )

    upper_lower_color = "[\"" + str(L[1]) + "\", \"" + str(L[2]) + "\"]"

    diary = MorningDiary(
        content=content,
        User_id=user.id,
        image_url=L[0],
        background_color=upper_lower_color,
        diary_name=diary_name,
        resolution=resolution,
        create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
        modify_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
    )
    try:
        db.add(diary)
        db.commit()
        chat = Chat(
            User_id=user.id,
            is_chatbot=True,
            MorningDiary_id=diary.id,
            create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
            content_type=1,
            content=diary_name,
            image_url=L[0],
        )
        db.add(chat)
        db.commit()
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
    try:
        chat = Chat(
            User_id=user.id,
            is_chatbot=False,
            create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
            content=content,
        )
        db.add(chat)
        db.commit()
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,  # 에러 메시지를 반환합니다.
        )
    # 그림과 일기의 제목을 생성합니다.
    L, diary_name = await asyncio.gather(
        generate_image(user.image_model, content),
        generate_diary_name(content)
    )

    upper_lower_color = "[\"" + str(L[1]) + "\", \"" + str(L[2]) + "\"]"

    # 저녁 일기를 생성합니다.
    diary = NightDiary(
        content=content,
        User_id=user.id,
        image_url=L[0],
        background_color=upper_lower_color,
        diary_name=diary_name,
        create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
        modify_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
    )
    try:
        db.add(diary)
        db.commit()
        chat = Chat(
            User_id=user.id,
            is_chatbot=True,
            NightDiary_id=diary.id,
            create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
            content_type=2,
            content=diary_name,
            image_url=L[0],
        )
        db.add(chat)
        db.commit()
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
    # 메모를 생성합니다.
    data = await send_gpt_request(6, content)
    data = json.loads(data)
    memo = Memo(
        title=data['title'],
        content=data['content'],
        User_id=user.id,
        create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
        modify_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
    )
    try:
        db.add(memo)
        db.commit()
        db.refresh(memo)
        chat = Chat(
            User_id=user.id,
            content=content,
            is_chatbot=False,
            create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
        )
        db.add(chat)
        db.commit()
        chat = Chat(
            User_id=user.id,
            is_chatbot=True,
            Memo_id=memo.id,
            create_date=datetime.datetime.now(pytz.timezone('Asia/Seoul')),
            content_type=3,
            content=data['title'],
        )
        db.add(chat)
        db.commit()
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
        start_time=body.start_time,
        end_time=body.end_time,
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
        calender.start_time = body.start_time
        calender.end_time = body.end_time
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

async def dairy_list(list_request: ListRequest, current_user: User, db: Session):
    page = list_request.page
    diary_type = list_request.diary_type
    limit = 6  # Number of records per page
    offset = (page - 1) * limit

    # 결과를 저장할 리스트
    result = [None] * 8  # [MorningDiary, MorningDiary_count, NightDiary, NightDiary_count, Memo, Memo_count, Calender, Calender_count]

    if diary_type == 0:
        # 모든 다이어리 타입을 불러옵니다.
        for idx, Model in enumerate([MorningDiary, NightDiary, Memo, Calender]):
            if idx == 3:
                data = db.query(Model).filter(Model.User_id == current_user.id, Model.is_deleted == False).order_by(
                    Model.start_time.desc()).limit(limit).offset(offset).all()
            else:
                data = db.query(Model).filter(Model.User_id == current_user.id, Model.is_deleted == False).order_by(
                    Model.create_date.desc()).limit(limit).offset(offset).all()
            count = db.query(Model).filter(Model.User_id == current_user.id, Model.is_deleted == False).count()
            result[idx * 2] = data
            result[idx * 2 + 1] = count
    elif diary_type in [1, 2, 3, 4]:
        # 특정 다이어리 타입만 불러옵니다.
        Model = [MorningDiary, NightDiary, Memo, Calender][diary_type - 1]
        if diary_type == 4:
            data = db.query(Model).filter(Model.User_id == current_user.id, Model.is_deleted == False).order_by(
                Model.start_time.desc()).limit(limit).offset(offset).all()
        else:
            data = db.query(Model).filter(Model.User_id == current_user.id, Model.is_deleted == False).order_by(
                Model.create_date.desc()).limit(limit).offset(offset).all()
        count = db.query(Model).filter(Model.User_id == current_user.id, Model.is_deleted == False).count()
        result[(diary_type - 1) * 2] = data
        result[(diary_type - 1) * 2 + 1] = count
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4000,
        )
    return result