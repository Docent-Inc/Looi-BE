from fastapi import HTTPException, status
from app.core.security import time_now
from app.db.database import save_db
from app.db.models import TextClassification, MorningDiary, NightDiary, Memo, Calender
from app.feature.aiRequset import send_gpt4_request
from app.feature.diary import create_morning_diary, create_night_diary, create_memo
from app.feature.generate import generate_schedule

async def classify_text(text, current_user, db):
    try:
        # 택스트 분류
        number = await send_gpt4_request(1, text, current_user, db)
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
    if text_type == 1:
        diary_id = await create_morning_diary(text, current_user, db)
        content = db.query(MorningDiary).filter(MorningDiary.id == diary_id).first()
    elif text_type == 2:
        diary_id = await create_night_diary(text, current_user, db)
        content = db.query(NightDiary).filter(NightDiary.id == diary_id).first()
    elif text_type == 3:
        diary_id = await create_memo(text, current_user, db)
        content = db.query(Memo).filter(Memo.id == diary_id).first()
    elif text_type == 4:
        diary_id = await generate_schedule(text, current_user, db)
        content = db.query(Calender).filter(Calender.id == diary_id).first()
    else:
        # 텍스트 분류 실패
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4013
        )
    return diary_id, content, text_type