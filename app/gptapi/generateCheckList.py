import asyncio
from app.gptapi.gptRequset import send_gpt_request
from app.db.database import get_db
from app.db.models.dream import DreamResolution
async def generate_checklist(TextId: int, dream: str, db: get_db()) -> str:
    '''
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
            {"role": "system", "content": "꿈 내용을 바탕으로 오늘 내가 체크해야될 내용 3개 만들어줘"},
            {"role": "system", "content": "제목없이 1. 2. 3. 로 적어줘"},
            {"role": "system", "content": "각 항목은 제목없이 내용만 적어줘, ~해보기, ~하기 등의 말투로 해줘"},
        ]
        response = await send_gpt_request(messages_prompt)
        return response

    dream_resolution, today_checklist = await asyncio.gather(
            get_dream_resolution(dream),
            get_today_checklist(dream)
    )
    '''
    dream_resolution = "test"
    today_checklist = "test"

    data = DreamResolution(
        Text_id=TextId,
        dream_resolution=dream_resolution,
        today_checklist=today_checklist
    )
    db.add(data)
    db.commit()
    db.refresh(data)

    return dream_resolution, today_checklist