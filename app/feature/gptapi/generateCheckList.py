import asyncio
from fastapi import HTTPException
from starlette import status
from app.feature.gptapi.generateImg import get_text_data
from app.feature.gptapi.gptRequset import send_gpt_request
from app.db.database import get_db
from app.db.models.dream import DreamResolution
async def generate_checklist(TextId: int, user_id: int, db: get_db()) -> str:
    async def get_dream_resolution(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "이 꿈을 간단하게 해몽해줘"},
            {"role": "system", "content": "존댓말을 사용해줘"},
            {"role": "system", "content": "max_length=60"},
            {"role": "user", "content": message}
        ]
        response = await send_gpt_request(messages_prompt)
        return response

    async def get_today_checklist(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "이 꿈의 내용을 바탕으로 현실에서 오늘 하루 체크해야될 내용 3개 만들어줘"},
            {"role": "system", "content": "~해보기, ~하기 와 같은 말투로, 1. 2. 3. 으로 나열해줘"},
            {"role": "system", "content": "max_length=100"},
            {"role": "user", "content": message},
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

    data = DreamResolution(
        Text_id=TextId,
        dream_resolution=dream_resolution,
        today_checklist=today_checklist
    )
    db.add(data)
    db.commit()
    db.refresh(data)

    return dream_resolution, today_checklist