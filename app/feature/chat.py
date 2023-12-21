from typing import Any

from fastapi import HTTPException, status
from app.core.security import time_now
from app.db.database import save_db
from app.db.models import TextClassification
from app.feature.aiRequset import GPTService
from app.feature.diary import create_morning_diary, create_memo_ai, create_night_diary_ai
from app.feature.generate import generate_schedule

async def classify_text(text_type, text, current_user, db):
    if text_type == 0:
        try:
            # 텍스트 분류
            gpt_service = GPTService(current_user, db)
            number = await gpt_service.send_gpt_request(1, text[:200])
            text_type = int(number.strip())
        except:
            # 텍스트 분류 실패
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4013
            )
    # 텍스트 저장
    text_type_dict = {1: "꿈", 2: "일기", 3: "메모", 4: "일정"}
    save_chat = TextClassification(
        text=text,
        User_id=current_user.id,
        text_type=text_type_dict[text_type],
        create_date=await time_now(),
    )
    save_db(save_chat, db)

    # 각 텍스트에 맞는 기능 실행
    diary = await generate_diary(text, text_type, current_user, db)
    return diary.id, diary, text_type

async def generate_diary(text, text_type, current_user, db) -> Any:
    if text_type == 1:
        diary = await create_morning_diary(text, current_user, db)
    elif text_type == 2:
        diary = await create_night_diary_ai(text, current_user, db)
    elif text_type == 3:
        diary = await create_memo_ai(text, current_user, db)
    elif text_type == 4:
        diary = await generate_schedule(text, current_user, db)
    else:
        # 텍스트 분류 실패
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4013
        )
    return diary