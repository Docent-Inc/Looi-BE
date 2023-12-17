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