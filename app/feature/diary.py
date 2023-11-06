import asyncio
from sqlalchemy import desc, literal
from sqlalchemy import null
from dateutil.relativedelta import relativedelta
from aiohttp import ClientSession
from fastapi import HTTPException
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import union_all
from starlette import status
from fastapi import BackgroundTasks

from app.core.security import time_now
from app.db.database import get_redis_client
from app.db.models import NightDiary, MorningDiary, Memo, Calender
from app.feature.aiRequset import send_gpt_request
from app.feature.generate import generate_image, generate_diary_name, generate_resolution_gpt
import datetime
import pytz

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
        'diary_name': cal.title,
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

async def create_morning_diary(content: str, user: User, db: Session, background_tasks: BackgroundTasks) -> int:
    mbti_content = content if user.mbti is None else user.mbti + ", " + content
    redis_client = await get_redis_client()
    now = await time_now()
    redis_key = "resolution:" + str(user.id) + ":" + now

    background_tasks.add_task(generate_resolution_gpt, mbti_content, user, db, redis_key)

    diary_name, L = await asyncio.gather(
        generate_diary_name(content, user, db),
        generate_image(user.image_model, content, user, db),
    )

    upper_lower_color = "[\"" + str(L[1]) + "\", \"" + str(L[2]) + "\"]"

    diary = MorningDiary(
        content=content,
        User_id=user.id,
        image_url=L[0],
        background_color=upper_lower_color,
        diary_name=diary_name,
        resolution="잠시만 기다려주세요. 꿈을 분석 중이에요!",
        create_date=await time_now(),
        modify_date=await time_now(),
    )
    db.add(diary)
    db.commit()
    await redis_client.set(redis_key, diary.id)
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

    # 저녁 일기를 생성합니다.
    diary = NightDiary(
        content=content,
        User_id=user.id,
        image_url=L[0],
        background_color=upper_lower_color,
        diary_name=diary_name,
        create_date=await time_now(),
        modify_date=await time_now(),
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
                data = {"title": "URL 주소", "content": content}
                print(data)
            else:
                data = {"title": title, "content": content}
    else:
        data = await send_gpt_request(6, content, user, db)
    memo = Memo(
        title=data['title'],
        content=data['content'],
        User_id=user.id,
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
    limit = 8  # 페이지당 레코드 수
    offset = (page - 1) * limit
    
    MorningDiary_count = db.query(MorningDiary).filter(MorningDiary.User_id == current_user.id, MorningDiary.is_deleted == False).count()
    NightDiary_count = db.query(NightDiary).filter(NightDiary.User_id == current_user.id, NightDiary.is_deleted == False).count()
    Memo_count = db.query(Memo).filter(Memo.User_id == current_user.id, Memo.is_deleted == False).count()


    # 모델의 열을 명시적으로 나열합니다.
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
        # Fetching all types of diaries.
        queries = []
        for idx, Model in enumerate([MorningDiary, NightDiary, Memo]):
            # You need to ensure 'create_date' is selected and labeled consistently across all queries.
            # Here, we are labeling it as 'common_create_date' for the union operation.
            query = db.query(*columns_list[idx], Model.create_date.label('common_create_date')).filter(
                Model.User_id == current_user.id,
                Model.is_deleted == False
            )
            query = query.order_by(Model.create_date.desc())
            queries.append(query)

        # Union all queries and the label will help in identifying the column in the merged table.
        unioned_queries = union_all(*queries).alias('unioned_queries')

        # Now you can safely order by the 'common_create_date', as it is consistently labeled in all subqueries.
        final_query = db.query(unioned_queries).order_by(desc(unioned_queries.c.common_create_date))
        final_query = final_query.limit(limit).offset(offset)  # Apply limit and offset after the order
        data_rows = db.execute(final_query).fetchall()

        for row in data_rows:
            parsed_row = {}
            for column, value in zip(unioned_queries.c, row):
                # 'diary_type'는 그대로 보존, 나머지 컬럼 이름에서 첫번째 밑줄 (_) 이후의 이름만 가져옵니다.
                key = column.key if column.key == 'diary_type' else column.key.split('_', 1)[-1]
                parsed_row[key] = value
            all_items.append(parsed_row)


    elif diary_type in [1, 2, 3]:
        Model = [MorningDiary, NightDiary, Memo][diary_type - 1]
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

    max_category = 0
    for item in all_items:
        if item['diary_type'] > max_category:
            max_category = item['diary_type']

    return {
        "list": all_items,
        "count": len(all_items),
        "max_category": max_category,
        "MoriningDiary_ratio": (MorningDiary_count / (MorningDiary_count + NightDiary_count + Memo_count)) * 100,
        "NightDiary_ratio": (NightDiary_count / (MorningDiary_count + NightDiary_count + Memo_count)) * 100,
        "Memo_ratio": (Memo_count / (MorningDiary_count + NightDiary_count + Memo_count)) * 100,
        "total_MorningDiary_count": MorningDiary_count,
        "total_NightDiary_count": NightDiary_count,
        "total_Memo_count": Memo_count,
    }

async def dairy_list_calender(list_request: CalenderListRequest, current_user: User, db: Session):
    if list_request.day is None:
        year = list_request.year
        month = list_request.month
        # year와 month를 받아서 해당 달의 일정을 모두 불러옵니다.
        calenders = db.query(Calender).filter(
            Calender.User_id == current_user.id,
            Calender.is_deleted == False,
            Calender.start_time >= datetime.datetime(year, month, 1),
            Calender.start_time < add_one_month(datetime.datetime(year, month, 1))
        ).all()
    else:
        year = list_request.year
        month = list_request.month
        day = list_request.day
        # year와 month를 받아서 해당 일의 일정을 모두 불러옵니다.
        calenders = db.query(Calender).filter(
            Calender.User_id == current_user.id,
            Calender.is_deleted == False,
            Calender.start_time >= datetime.datetime(year, month, day),
            Calender.start_time < datetime.datetime(year, month, day) + datetime.timedelta(days=1)
        ).all()
    today = await time_now()
    today_count = db.query(Calender).filter(
        Calender.User_id == current_user.id,
        Calender.is_deleted == False,
        Calender.start_time >= datetime.datetime(today.year, today.month, today.day),
        Calender.start_time < datetime.datetime(today.year, today.month, today.day) + datetime.timedelta(days=1)
    ).count()

    calenders_transformed = [transform_calendar(cal) for cal in calenders]
    return today_count, calenders_transformed
