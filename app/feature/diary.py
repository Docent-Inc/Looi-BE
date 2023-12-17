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
import datetime
from app.schemas.request import UpdateDiaryRequest, CalenderRequest, ListRequest, CalenderListRequest, MemoRequest, \
    CreateNightDiaryRequest
from app.schemas.response import User

async def add_one_month(original_date):
    return original_date + relativedelta(months=1)
async def transform_calendar(cal):
    return {
        'id': cal.id,
        'User_id': cal.User_id,
        'start_time': cal.start_time,
        'end_time': cal.end_time,
        'title': cal.title,
        'content': cal.content,
        'is_deleted': cal.is_deleted
    }
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

async def create_morning_diary(content: str, user: User, db: Session) -> MorningDiary:

    # 사용자의 mbti와 content를 합친 문자열 생성
    mbti_content = content if user.mbti is None else user.mbti + ", " + content

    # 다이어리 제목, 이미지, 해몽 생성
    gpt_service = GPTService(user, db)
    diary_name, image_url, resolution = await asyncio.gather(
        gpt_service.send_gpt_request(2, content),
        gpt_service.send_dalle_request(content),
        gpt_service.send_gpt_request(5, mbti_content)
    )

    # 이미지 배경색 추출
    upper_dominant_color, lower_dominant_color = await image_background_color(image_url)

    # 이미지 background color 문자열로 변환
    upper_lower_color = "[\"" + str(upper_dominant_color) + "\", \"" + str(lower_dominant_color) + "\"]"

    # db에 저장
    await check_length(diary_name, 255, 4023)
    await check_length(content, 1000, 4221)
    now = await time_now()
    resolution = json.loads(resolution)
    try:
        diary = MorningDiary(
            content=content,
            User_id=user.id,
            image_url=image_url,
            background_color=upper_lower_color,
            diary_name=diary_name,
            resolution=resolution['resolution'],
            main_keyword=json.dumps(resolution["main_keywords"], ensure_ascii=False),
            create_date=now,
            modify_date=now,
        )
        diary = save_db(diary, db)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4021,
        )

    # 다이어리 반환
    return diary

async def read_morning_diary(diary_id: int, user:User, db: Session) -> MorningDiary:

    # 다이어리 조회
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.User_id == user.id, MorningDiary.is_deleted == False).first()

    # 다이어리가 없을 경우 예외 처리
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )

    # 조회수 증가
    diary.view_count += 1
    diary = save_db(diary, db)

    # 다이어리 반환
    return diary
async def share_read_morning_diary(diary_id: int, db: Session) -> MorningDiary:

    # 다이어리 조회
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.is_deleted == False).first()

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

async def update_morning_diary(diary_id: int, content: UpdateDiaryRequest, user: User, db: Session) -> int:

    # 다이어리 조회
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.User_id == user.id, MorningDiary.is_deleted == False).first()

    # 다이어리가 없을 경우 예외 처리
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )

    if content.diary_name != "":
        await check_length(content.diary_name, 255, 4023)
        diary.diary_name = content.diary_name
    if content.content != "":
        await check_length(content.content, 1000, 4221)
        diary.content = content.content

    diary.modify_date = await time_now()
    diary = save_db(diary, db)

    # 다이어리 반환
    return diary

async def delete_morning_diary(diary_id: int, user: User, db: Session):

    # 다이어리 조회
    diary = db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.User_id == user.id, MorningDiary.is_deleted == False).first()

    # 다이어리가 없을 경우 예외 처리
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4011,
        )

    # 다이어리 삭제
    diary.is_deleted = True
    save_db(diary, db)
async def list_morning_diary(page: int, user: User, db: Session):

    # 다이어리 목록 조회
    limit = 5
    diaries = db.query(MorningDiary).filter(MorningDiary.User_id == user.id, MorningDiary.is_deleted == False).order_by(MorningDiary.create_date.desc()).limit(limit).offset((page-1)*limit).all()

    # 다이어리 목록 반환
    return diaries

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

async def create_night_diary(body: CreateNightDiaryRequest, user: User, db: Session):
    gpt_service = GPTService(user, db)
    if body.title == "":
        # 이미지와 다이어리 제목 생성
        content = body.content
        image_url, diary_name = await asyncio.gather(
            gpt_service.send_dalle_request(content),
            gpt_service.send_gpt_request(2, content)
        )
    else:
        diary_name = body.title
        content = body.content
        image_url = await gpt_service.send_dalle_request(content)

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
        create_date=body.date,
        modify_date=now,
    )
    diary = save_db(diary, db)

    # 다이어리 반환
    return diary

async def read_night_diary(diary_id: int, user:User, db: Session) -> NightDiary:

    # 다이어리 조회
    diary = db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == user.id, NightDiary.is_deleted == False).first()

    # 다이어리가 없을 경우 예외 처리
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4012,
        )

    # 조회수 증가
    diary.view_count += 1
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

async def update_night_diary(diary_id: int, content: UpdateDiaryRequest, user: User, db: Session) -> int:

    # 다이어리 조회
    diary = db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == user.id, NightDiary.is_deleted == False).first()

    # 다이어리가 없을 경우 예외 처리
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4012,
        )

    if content.diary_name != "":
        await check_length(content.diary_name, 255, 4023)
        diary.diary_name = content.diary_name
    if content.content != "":
        await check_length(content.content, 1000, 4221)
        diary.content = content.content
    diary.modify_date = await time_now()
    diary = save_db(diary, db)

    # 다이어리 반환
    return diary

async def delete_night_diary(diary_id: int, user: User, db: Session) -> int:

    # 다이어리 조회
    diary = db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == user.id, NightDiary.is_deleted == False).first()

    # 다이어리가 없을 경우 예외 처리
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4012,
        )
    # 다이어리 삭제
    diary.is_deleted = True
    save_db(diary, db)

async def list_night_diary(page: int, user: User, db: Session):

    # 다이어리 목록 조회
    limit = 5
    diaries = db.query(NightDiary).filter(NightDiary.User_id == user.id, NightDiary.is_deleted == False).order_by(NightDiary.create_date.desc()).limit(limit).offset((page-1)*limit).all()

    # 다이어리 목록 반환
    return diaries
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

async def create_memo(
    body: MemoRequest = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Memo:
    content = body.content

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

    # 제목이 없다면 자동 생성
    if body.title == "":
        body.title = data['title']

    # 제목, 내용 길이 체크
    await check_length(text=body.title, max_length=255, error_code=4023)
    await check_length(text=body.content, max_length=1000, error_code=4221)

    # 메모 생성
    now = await time_now()
    memo = Memo(
        title=body.title,
        content=content,
        User_id=user.id,
        tags=json.dumps(data['tags'], ensure_ascii=False),
        create_date=now,
        modify_date=now,
    )
    memo = save_db(memo, db)

    # 메모 반환
    return memo


async def read_memo(
    memo_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Memo:

    # 메모 조회
    memo = db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == user.id, Memo.is_deleted == False).first()

    # 메모가 없을 경우 예외 처리
    if not memo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4016,
        )

    # 메모 반환
    return memo

async def update_memo(
    memo_id: int,
    body: MemoRequest = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Memo:

    # 메모 조회
    memo = db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == user.id, Memo.is_deleted == False).first()

    # 메모가 없을 경우 예외 처리
    if not memo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4016,
        )

    # 제목, 내용 길이 체크
    await check_length(text=body.title, max_length=255, error_code=4023)
    await check_length(text=body.content, max_length=1000, error_code=4221)

    # 메모 수정
    memo.title = body.title
    memo.content = body.content
    memo.modify_date = await time_now()
    memo = save_db(memo, db)

    # 메모 반환
    return memo

async def delete_memo(
    memo_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:

    # 메모 조회
    memo = db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == user.id, Memo.is_deleted == False).first()

    # 메모가 없을 경우 예외 처리
    if not memo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4016,
        )

    # 메모 삭제
    memo.is_deleted = True
    save_db(memo, db)


async def create_calender(body: CalenderRequest, user: User, db: Session) -> Calender:
    if body.start_time >= body.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4022,
        )
    if body.title == "":
        gpt_service = GPTService(user, db)
        body.title = await gpt_service.send_gpt_request(9, body.content)

    # 캘린더 생성
    await check_length(text=body.title, max_length=255, error_code=4023)
    await check_length(text=body.content, max_length=255, error_code=4023)
    now = await time_now()
    calender = Calender(
        User_id=user.id,
        start_time=body.start_time,
        end_time=body.end_time,
        title=body.title,
        content=body.content,
        create_date=now,
    )
    # 캘린더 저장
    calender = save_db(calender, db)

    # 캘린더 반환
    return calender

async def read_calender(calender_id: int, user: User, db: Session) -> Calender:

    # 캘린더 조회
    calender = db.query(Calender).filter(Calender.id == calender_id, Calender.User_id == user.id, Calender.is_deleted == False).first()

    # 캘린더가 없을 경우 예외 처리
    if not calender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4015,
        )

    # 캘린더 반환
    return calender

async def update_calender(calender_id: int, body: CalenderRequest, user: User, db: Session) -> int:

    # 캘린더 조회
    calender = db.query(Calender).filter(Calender.id == calender_id, Calender.User_id == user.id, Calender.is_deleted == False).first()

    # 캘린더가 없을 경우 예외 처리
    if not calender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4015,
        )

    # 캘린더 수정
    calender.start_time = body.start_time
    calender.end_time = body.end_time
    calender.title = body.title
    calender.content = body.content
    calender = save_db(calender, db)

    return calender

async def delete_calender(calender_id: int, user: User, db: Session):

    # 캘린더 조회
    calender = db.query(Calender).filter(Calender.id == calender_id, Calender.User_id == user.id, Calender.is_deleted == False).first()

    # 캘린더가 없을 경우 예외 처리
    if not calender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4015,
        )

    # 캘린더 삭제
    calender.is_deleted = True
    save_db(calender, db)

async def dairy_list(list_request: ListRequest, current_user: User, db: Session):

    # diary_type에 따라 쿼리 변경
    page = list_request.page
    diary_type = list_request.diary_type
    if page == 1:
        limit = 7
        offset = 0
    else:
        limit = 8
        offset = 7 + (page - 2) * limit

    # morning diary columns
    morning_diary_columns = [
        MorningDiary.id, MorningDiary.User_id, MorningDiary.diary_name, MorningDiary.content,
        MorningDiary.resolution, MorningDiary.image_url, MorningDiary.background_color,
        MorningDiary.create_date, MorningDiary.modify_date, MorningDiary.is_deleted
    ]

    # night diary columns
    night_diary_columns = [
        NightDiary.id, NightDiary.User_id, NightDiary.diary_name, NightDiary.content,
        null().label('resolution'), NightDiary.image_url, NightDiary.background_color,
        NightDiary.create_date, NightDiary.modify_date, NightDiary.is_deleted
    ]

    # memo columns
    memo_columns = [
        Memo.id, Memo.User_id, Memo.title, Memo.content,
        null().label('resolution'), null().label('image_url'), null().label('background_color'),
        Memo.create_date, Memo.modify_date, Memo.is_deleted
    ]

    # diary_type에 따라 diary_type 컬럼 추가
    morning_diary_columns.append(literal(1).label('diary_type'))
    night_diary_columns.append(literal(2).label('diary_type'))
    memo_columns.append(literal(3).label('diary_type'))

    # diary_type에 따라 쿼리 변경
    columns_list = [morning_diary_columns, night_diary_columns, memo_columns]
    all_items = []

    # diary_type이 0일 경우 모든 다이어리 조회
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

        # 전체 다이어리 개수
        total_count = db.query(MorningDiary.id).filter(MorningDiary.User_id == current_user.id, MorningDiary.is_deleted == False).count() + \
                        db.query(NightDiary.id).filter(NightDiary.User_id == current_user.id, NightDiary.is_deleted == False).count() + \
                        db.query(Memo.id).filter(Memo.User_id == current_user.id, Memo.is_deleted == False).count()

    # diary_type이 1, 2, 3일 경우 각각의 다이어리 조회
    elif diary_type in [1, 2, 3]:
        # diary_type에 따라 Model 변경
        Model = [MorningDiary, NightDiary, Memo][diary_type - 1]
        total_count = db.query(func.count(Model.id)).filter(Model.User_id == current_user.id, Model.is_deleted == False).scalar()
        data_rows = db.query(Model).filter(Model.User_id == current_user.id, Model.is_deleted == False).order_by(Model.create_date.desc()).limit(limit).offset(offset).all()

        for item in data_rows:
            if hasattr(item, 'as_dict'):
                item_dict = item.as_dict()
                item_dict['diary_type'] = diary_type
                all_items.append(item_dict)
        if diary_type == 3:
            all_items = [await transform_memo(cal) for cal in all_items]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4000,
        )
    return all_items, len(all_items), total_count

async def dairy_list_calender(list_request: CalenderListRequest, current_user: User, db: Session):
    if list_request.day is None:
        year = list_request.year
        month = list_request.month
        start_of_month = datetime.datetime(year, month, 1)
        end_of_month = await add_one_month(start_of_month)

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

    calenders_transformed = [await transform_calendar(cal) for cal in calenders]
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