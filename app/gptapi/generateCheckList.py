import asyncio

from fastapi import HTTPException
from starlette import status

from app.gptapi.generateImg import get_text_data
from app.gptapi.gptRequset import send_gpt_request
from app.db.database import get_db
from app.db.models.dream import DreamResolution
async def generate_checklist(TextId: int, user_id: int, db: get_db()) -> str:
    async def get_dream_resolution(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": message},
            {"role": "system", "content": "꿈 내용을 바탕으로 꿈 해몽을 만들어줘"},
            {"role": "system", "content": "꿈 해몽은 100자 정도로 만들어줘"},
            {"role": "system", "content": "존댓말로 만들어줘"},
        ]
        response = await send_gpt_request(messages_prompt)
        return response

    async def get_today_checklist(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": message},
            {"role": "system", "content": "꿈 내용을 바탕으로 오늘 현실에서 내가 체크해야될 내용 3개 만들어줘"},
            {"role": "system", "content": "제목없이 1. 2. 3. 로 적어줘"},
            {"role": "system", "content": "도전해볼 내용 두 개, 조심해야될 내용 한 개 적어줘"},
            {"role": "system", "content": "각 항목은 제목없이 내용만 적어줘, ~해보기, ~하기 등의 말투로 해줘"},
        ]
        response = await send_gpt_request(messages_prompt)
        return response

    # 데이터베이스에서 textId와 current_user.id를 확인 후 dream 가져오기
    text_data = await get_text_data(TextId, user_id, db)
    if text_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="생성된 꿈이 없습니다.")

    dream = text_data.dream  # 생성된 꿈 정보 불러오기

    dream_resolution, today_checklist = await asyncio.gather(
            get_dream_resolution(dream),
            get_today_checklist(dream)
    )
    # dream_resolution = "test"
    # today_checklist = "test"

    data = DreamResolution(
        Text_id=TextId,
        dream_resolution=dream_resolution,
        today_checklist=today_checklist
    )
    db.add(data)
    db.commit()
    db.refresh(data)

    return dream_resolution, today_checklist