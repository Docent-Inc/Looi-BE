import asyncio
import json
from sqlalchemy import desc, literal, func, or_, and_
from sqlalchemy import null
from dateutil.relativedelta import relativedelta
from aiohttp import ClientSession
from fastapi import HTTPException, Depends, Body, Path
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import union_all
from starlette import status
from app.core.security import time_now, get_current_user, check_length
from app.db.database import save_db, get_db
from app.db.models import NightDiary, MorningDiary, Memo, Calender
from app.feature.aiRequset import GPTService
from app.feature.generate import image_background_color
from app.schemas.response import User
async def transform_memo(memo):
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

async def create_night_diary_ai(content: str, user: User, db: Session):
    # 이미지와 다이어리 제목 생성
    gpt_service = GPTService(user, db)
    image_url, diary_name = await asyncio.gather(
        gpt_service.send_dalle_request(content),
        gpt_service.send_gpt_request(2, content)
    )

    # 이미지 배경색 추출
    upper_dominant_color, lower_dominant_color = await image_background_color(image_url)

    # 이미지 background color 문자열로 변환
    upper_lower_color = "[\"" + str(upper_dominant_color) + "\", \"" + str(lower_dominant_color) + "\"]"

    # 저녁 일기 db에 저장
    await check_length(diary_name, 255, 4023)
    await check_length(content, 1000, 4221)
    now = await time_now()
    diary = NightDiary(
        content=content,
        User_id=user.id,
        image_url=image_url,
        background_color=upper_lower_color,
        diary_name=diary_name,
        create_date=now,
        modify_date=now,
    )
    diary = save_db(diary, db)

    # 다이어리 반환
    return diary



async def share_read_night_diary(diary_id: int, db: Session) -> NightDiary:

    # 다이어리 조회
    diary = db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.is_deleted == False).first()

    # 다이어리가 없을 경우 예외 처리
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )

    # 조회수 증가
    diary.share_count += 1
    diary = save_db(diary, db)

    # 다이어리 반환
    diary.User_id = None
    return diary

async def fetch_content_from_url(session: ClientSession, url: str) -> str:
    # url로부터 html content를 가져옴
    async with session.get(url) as response:
        return await response.text()
async def create_memo_ai(content: str, user: User, db: Session) -> int:
    # url이면 title을 가져옴
    if content.startswith('http://') or content.startswith('https://'):
        async with ClientSession() as session:
            html_content = await fetch_content_from_url(session, content)
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string if soup.title else "No title"
            if title == "No title":
                content = f"title = URL 주소, content = {content}"
            else:
                content = f"title = {title}, content = {content}"

    # gpt-3.5 요청
    gpt_service = GPTService(user, db)
    data = await gpt_service.send_gpt_request(8, content)
    data = json.loads(data)

    # 메모 생성
    now = await time_now()
    memo = Memo(
        title=data['title'],
        content=content,
        User_id=user.id,
        tags=json.dumps(data['tags'], ensure_ascii=False),
        create_date=now,
        modify_date=now,
    )
    memo = save_db(memo, db)

    # 메모 id 반환
    return memo

# async def dairy_list(list_request: ListRequest, current_user: User, db: Session):
#
#     # diary_type에 따라 쿼리 변경
#     page = list_request.page
#     diary_type = list_request.diary_type
#     limit = 8
#     offset = (page - 1) * limit
#
#     # morning diary columns
#     morning_diary_columns = [
#         MorningDiary.id, MorningDiary.User_id, MorningDiary.diary_name, MorningDiary.content,
#         MorningDiary.resolution, MorningDiary.image_url, MorningDiary.background_color,
#         MorningDiary.create_date, MorningDiary.modify_date, MorningDiary.is_deleted
#     ]
#
#     # night diary columns
#     night_diary_columns = [
#         NightDiary.id, NightDiary.User_id, NightDiary.diary_name, NightDiary.content,
#         null().label('resolution'), NightDiary.image_url, NightDiary.background_color,
#         NightDiary.create_date, NightDiary.modify_date, NightDiary.is_deleted
#     ]
#
#     # memo columns
#     memo_columns = [
#         Memo.id, Memo.User_id, Memo.title, Memo.content,
#         null().label('resolution'), null().label('image_url'), null().label('background_color'),
#         Memo.create_date, Memo.modify_date, Memo.is_deleted
#     ]
#
#     # diary_type에 따라 diary_type 컬럼 추가
#     morning_diary_columns.append(literal(1).label('diary_type'))
#     night_diary_columns.append(literal(2).label('diary_type'))
#     memo_columns.append(literal(3).label('diary_type'))
#
#     # diary_type에 따라 쿼리 변경
#     columns_list = [morning_diary_columns, night_diary_columns, memo_columns]
#     all_items = []
#
#     # diary_type이 0일 경우 모든 다이어리 조회
#     if diary_type == 0:
#         queries = []
#         for idx, Model in enumerate([MorningDiary, NightDiary, Memo]):
#             query = db.query(*columns_list[idx], Model.create_date.label('common_create_date')).filter(
#                 Model.User_id == current_user.id,
#                 Model.is_deleted == False
#             )
#             query = query.order_by(Model.create_date.desc())
#             queries.append(query)
#         unioned_queries = union_all(*queries).alias('unioned_queries')
#         final_query = db.query(unioned_queries).order_by(desc(unioned_queries.c.common_create_date))
#         final_query = final_query.limit(limit).offset(offset)
#         data_rows = db.execute(final_query).fetchall()
#
#         for row in data_rows:
#             parsed_row = {}
#             for column, value in zip(unioned_queries.c, row):
#                 # 'diary_type'는 그대로 보존, 나머지 컬럼 이름에서 첫번째 밑줄 (_) 이후의 이름만 가져옵니다.
#                 key = column.key if column.key == 'diary_type' else column.key.split('_', 1)[-1]
#                 parsed_row[key] = value
#             all_items.append(parsed_row)
#
#         # 전체 다이어리 개수
#         total_count = db.query(MorningDiary.id).filter(MorningDiary.User_id == current_user.id, MorningDiary.is_deleted == False).count() + \
#                         db.query(NightDiary.id).filter(NightDiary.User_id == current_user.id, NightDiary.is_deleted == False).count() + \
#                         db.query(Memo.id).filter(Memo.User_id == current_user.id, Memo.is_deleted == False).count()
#
#     # diary_type이 1, 2, 3일 경우 각각의 다이어리 조회
#     elif diary_type in [1, 2, 3]:
#         # diary_type에 따라 Model 변경
#         Model = [MorningDiary, NightDiary, Memo][diary_type - 1]
#         total_count = db.query(func.count(Model.id)).filter(Model.User_id == current_user.id, Model.is_deleted == False).scalar()
#         data_rows = db.query(Model).filter(Model.User_id == current_user.id, Model.is_deleted == False).order_by(Model.create_date.desc()).limit(limit).offset(offset).all()
#
#         for item in data_rows:
#             if hasattr(item, 'as_dict'):
#                 item_dict = item.as_dict()
#                 item_dict['diary_type'] = diary_type
#                 all_items.append(item_dict)
#         if diary_type == 3:
#             all_items = [await transform_memo(cal) for cal in all_items]
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=4000,
#         )
#     return all_items, len(all_items), total_count


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