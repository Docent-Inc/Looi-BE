import asyncio
import json
from sqlalchemy import desc, literal, func, or_, and_
from sqlalchemy import null
from dateutil.relativedelta import relativedelta
from aiohttp import ClientSession
from fastapi import HTTPException
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import union_all
from starlette import status
from app.core.security import time_now
from app.db.models import NightDiary, MorningDiary, Memo, Calender
from app.feature.aiRequset import send_gpt_request
from app.feature.generate import generate_image, generate_diary_name, generate_resolution_gpt
import datetime
from app.schemas.request import UpdateDiaryRequest, CalenderRequest, ListRequest, CalenderListRequest
from app.schemas.response import User

def add_one_month(original_date):
    return original_date + relativedelta(months=1)
def transform_calendar(cal):
    return {
        'id': cal.id,
        'User_id': cal.User_id,
        'start_time': cal.start_time,
        'end_time': cal.end_time,
        'title': cal.title,
        'content': cal.content,
        'is_deleted': cal.is_deleted
    }
def transform_memo(memo):
    return {
        'id': memo['id'],
        'User_id': memo['User_id'],
        'diary_name': memo['title'],
        'content': memo['content'],
        'diary_type': memo['diary_type'],
        'create_date': memo['create_date'],
        'modify_date': memo['modify_date'],
        'is_deleted': memo['is_deleted']
    }

async def create_morning_diary(content: str, user: User, db: Session) -> int:
    mbti_content = content if user.mbti is None else user.mbti + ", " + content
    diary_name, L, resolution = await asyncio.gather(
        generate_diary_name(content, user, db),
        generate_image(user.image_model, content, user, db),
        generate_resolution_gpt(mbti_content, user, db)
    )
    upper_lower_color = "[\"" + str(L[1]) + "\", \"" + str(L[2]) + "\"]"
    now = await time_now()

    diary = MorningDiary(
        content=content,
        User_id=user.id,
        image_url=L[0],
        background_color=upper_lower_color,
        diary_name=diary_name,
        resolution=resolution['resolution'],
        main_keyword=json.dumps(resolution["main_keywords"], ensure_ascii=False),
        create_date=now,
        modify_date=now,
    )
    db.add(diary)
    db.commit()
    return diary.id

async def read_morning_diary(diary_id: int, user:User, db: Session) -> MorningDiary:
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.User_id == user.id, MorningDiary.is_deleted == False).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )
    return diary
async def share_read_morning_diary(diary_id: int, db: Session) -> MorningDiary:
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.is_deleted == False).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )
    diary.User_id = None
    return diary

async def share_read_night_diary(diary_id: int, db: Session) -> NightDiary:
    diary = db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.is_deleted == False).first()
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )
    diary.User_id = None
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
        diary.modify_date = await time_now()
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
    L, diary_name = await asyncio.gather(
        generate_image(user.image_model, content, user, db),
        generate_diary_name(content, user, db)
    )

    upper_lower_color = "[\"" + str(L[1]) + "\", \"" + str(L[2]) + "\"]"
    now = await time_now()

    # 저녁 일기를 생성합니다.
    diary = NightDiary(
        content=content,
        User_id=user.id,
        image_url=L[0],
        background_color=upper_lower_color,
        diary_name=diary_name,
        create_date=now,
        modify_date=now,
    )
    try:
        db.add(diary)
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
        diary.modify_date = await time_now()
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
    async def fetch_content_from_url(session: ClientSession, url: str) -> str:
        async with session.get(url) as response:
            return await response.text()
    # 메모를 생성합니다.
    if content.startswith('http://') or content.startswith('https://'):
        async with ClientSession() as session:
            html_content = await fetch_content_from_url(session, content)
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string if soup.title else "No title"
            if title == "No title":
                content = f"title = URL 주소, content = {content}"
            else:
                content = f"title = {title}, content = {content}"

    data = await send_gpt_request(6, content, user, db)
    memo = Memo(
        title=data['title'],
        content=data['content'],
        User_id=user.id,
        tags=json.dumps(data['tags'], ensure_ascii=False),
        create_date=await time_now(),
        modify_date=await time_now(),
    )
    db.add(memo)
    db.commit()
    db.refresh(memo)
    return memo.id

async def read_memo(memo_id: int, user: User, db: Session) -> Memo:
    memo = db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == user.id, Memo.is_deleted == False).first()
    if not memo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4016,
        )
    return memo

async def delete_memo(memo_id: int, user: User, db: Session) -> int:
    memo = db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == user.id, Memo.is_deleted == False).first()
    if not memo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4016,
        )
    try:
        memo.is_deleted = True
        db.commit()
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )

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
    limit = 8
    offset = (page - 1) * limit

    morning_diary_columns = [
        MorningDiary.id, MorningDiary.User_id, MorningDiary.diary_name, MorningDiary.content,
        MorningDiary.resolution, MorningDiary.image_url, MorningDiary.background_color,
        MorningDiary.create_date, MorningDiary.modify_date, MorningDiary.is_deleted
    ]

    night_diary_columns = [
        NightDiary.id, NightDiary.User_id, NightDiary.diary_name, NightDiary.content,
        null().label('resolution'), NightDiary.image_url, NightDiary.background_color,
        NightDiary.create_date, NightDiary.modify_date, NightDiary.is_deleted
    ]

    memo_columns = [
        Memo.id, Memo.User_id, Memo.title, Memo.content,
        null().label('resolution'), null().label('image_url'), null().label('background_color'),
        Memo.create_date, Memo.modify_date, Memo.is_deleted
    ]

    morning_diary_columns.append(literal(1).label('diary_type'))
    night_diary_columns.append(literal(2).label('diary_type'))
    memo_columns.append(literal(3).label('diary_type'))

    columns_list = [morning_diary_columns, night_diary_columns, memo_columns]
    all_items = []

    if diary_type == 0:
        queries = []
        for idx, Model in enumerate([MorningDiary, NightDiary, Memo]):
            query = db.query(*columns_list[idx], Model.create_date.label('common_create_date')).filter(
                Model.User_id == current_user.id,
                Model.is_deleted == False
            )
            query = query.order_by(Model.create_date.desc())
            queries.append(query)
        unioned_queries = union_all(*queries).alias('unioned_queries')
        final_query = db.query(unioned_queries).order_by(desc(unioned_queries.c.common_create_date))
        final_query = final_query.limit(limit).offset(offset)
        data_rows = db.execute(final_query).fetchall()

        for row in data_rows:
            parsed_row = {}
            for column, value in zip(unioned_queries.c, row):
                # 'diary_type'는 그대로 보존, 나머지 컬럼 이름에서 첫번째 밑줄 (_) 이후의 이름만 가져옵니다.
                key = column.key if column.key == 'diary_type' else column.key.split('_', 1)[-1]
                parsed_row[key] = value
            all_items.append(parsed_row)
        total_count = db.query(MorningDiary.id).filter(MorningDiary.User_id == current_user.id, MorningDiary.is_deleted == False).count() + \
                        db.query(NightDiary.id).filter(NightDiary.User_id == current_user.id, NightDiary.is_deleted == False).count() + \
                        db.query(Memo.id).filter(Memo.User_id == current_user.id, Memo.is_deleted == False).count()


    elif diary_type in [1, 2, 3]:
        Model = [MorningDiary, NightDiary, Memo][diary_type - 1]
        total_count = db.query(func.count(Model.id)).filter(Model.User_id == current_user.id, Model.is_deleted == False).scalar()
        data_rows = db.query(Model).filter(Model.User_id == current_user.id, Model.is_deleted == False).order_by(Model.create_date.desc()).limit(limit).offset(offset).all()

        for item in data_rows:
            if hasattr(item, 'as_dict'):
                item_dict = item.as_dict()
                item_dict['diary_type'] = diary_type
                all_items.append(item_dict)
        if diary_type == 3:
            all_items = [transform_memo(cal) for cal in all_items]

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4000,
        )
    return {
        "list": all_items,
        "count": len(all_items),
        "total_count": total_count,
    }

async def dairy_list_calender(list_request: CalenderListRequest, current_user: User, db: Session):
    if list_request.day is None:
        year = list_request.year
        month = list_request.month
        start_of_month = datetime.datetime(year, month, 1)
        end_of_month = add_one_month(start_of_month)

        calenders = db.query(Calender).filter(
            Calender.User_id == current_user.id,
            Calender.is_deleted == False,
            or_(
                Calender.start_time.between(start_of_month, end_of_month),
                Calender.end_time.between(start_of_month, end_of_month)
            )
        ).order_by(Calender.start_time).all()
    else:
        year = list_request.year
        month = list_request.month
        day = list_request.day
        start_of_day = datetime.datetime(year, month, day)
        end_of_day = start_of_day + datetime.timedelta(days=1)
        calenders = db.query(Calender).filter(
            Calender.User_id == current_user.id,
            Calender.is_deleted == False,
            or_(
                and_(Calender.start_time >= start_of_day, Calender.start_time < end_of_day),
                and_(Calender.end_time > start_of_day, Calender.end_time <= end_of_day),
                and_(Calender.start_time <= start_of_day, Calender.end_time >= end_of_day)
            )
        ).order_by(Calender.start_time).all()
    today = await time_now()
    start_of_today = datetime.datetime(today.year, today.month, today.day)
    end_of_today = start_of_today + datetime.timedelta(days=1)

    today_count = db.query(Calender).filter(
        Calender.User_id == current_user.id,
        Calender.is_deleted == False,
        or_(
            and_(Calender.start_time >= start_of_today, Calender.start_time < end_of_today),
            and_(Calender.end_time > start_of_today, Calender.end_time <= end_of_today),
            and_(Calender.start_time <= start_of_today, Calender.end_time >= end_of_today)
        )
    ).count()

    calenders_transformed = [transform_calendar(cal) for cal in calenders]
    return today_count, calenders_transformed

async def get_diary_ratio(user: User, db: Session):
    MorningDiary_count = db.query(MorningDiary).filter(MorningDiary.User_id == user.id,
                                                       MorningDiary.is_deleted == False).count()
    NightDiary_count = db.query(NightDiary).filter(NightDiary.User_id == user.id,
                                                   NightDiary.is_deleted == False).count()
    Memo_count = db.query(Memo).filter(Memo.User_id == user.id, Memo.is_deleted == False).count()

    total = MorningDiary_count + NightDiary_count + Memo_count
    if total == 0:
        morning_diary_ratio = 0
        night_diary_ratio = 0
        memo_ratio = 0
        max_category = 0
    else:
        morning_diary_ratio = (MorningDiary_count / total) * 100
        night_diary_ratio = (NightDiary_count / total) * 100
        memo_ratio = (Memo_count / total) * 100

    max_category_value = max(morning_diary_ratio, night_diary_ratio, memo_ratio)
    if total == 0:
        pass
    elif morning_diary_ratio == night_diary_ratio and night_diary_ratio == memo_ratio:
        max_category = 4
    elif max_category_value == morning_diary_ratio:
        max_category = 1
    elif max_category_value == night_diary_ratio:
        max_category = 2
    elif max_category_value == memo_ratio:
        max_category = 3

    return {
        "max_category": max_category,
        "morning_diary_count": MorningDiary_count,
        "night_diary_count": NightDiary_count,
        "memo_count": Memo_count,
        "morning_diary_ratio": morning_diary_ratio,
        "night_diary_ratio": night_diary_ratio,
        "memo_ratio": memo_ratio,
    }