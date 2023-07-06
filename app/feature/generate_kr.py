import asyncio
from app.core.current_time import get_current_time
from app.feature.gptapi.generateImg import generate_img
from app.db.models.dream import DreamText, DreamImage
from app.db.database import get_db
from app.feature.gptapi.gptRequset import send_gpt_request, send_bard_request


async def generate_text(text: str, userId: int, db: get_db()) -> str:
    async def get_dreamName(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "꿈의 내용을 이해하고 너가 재미있는 꿈의 제목을 만들어줘"},
            {"role": "user", "content": message}
        ]
        dreamName = await send_gpt_request(messages_prompt)
        return dreamName

    async def DALLE2(message: str):
        messages_prompt = [
            {"role": "system", "content": "Understand this dream and make just one scene a prompt for DALLE2"},
            {"role": "system", "content": "include the word illustration and 7 world about Subject, Medium, Environment, Lighting, Color, Mood, Compoition"},
            {"role": "system", "content": "make just prompt only engilsh"},
            {"role": "system", "content": "max_length=100"},
            {"role": "user", "content": message}
        ]
        prompt = await send_gpt_request(messages_prompt)

        dream_image_url = await generate_img(prompt, userId)
        return dream_image_url, prompt

    dream_name, L = await asyncio.gather(
        get_dreamName(text),
        DALLE2(text)
    )
    dream = text
    dream_image_url, dream_image_prompt = L

    # 데이터베이스에 DreamText 저장하기
    dream_text = DreamText(
        User_id=userId,
        User_text=text,
        dream_name=dream_name,
        dream=dream,
        DALLE2=dream_image_prompt,
        date=get_current_time(),
        is_deleted=False
    )
    db.add(dream_text)
    db.commit()
    db.refresh(dream_text)

    # 데이터베이스에 DreamImage 저장하기
    dream_image = DreamImage(
        Text_id=dream_text.id,
        dream_image_url=dream_image_url
    )
    db.add(dream_image)
    db.commit()
    db.refresh(dream_image)
    # 데이터베이스에서 id값 찾기
    dream_text_id = dream_text.id

    return dream_text_id, dream_name, dream, dream_image_url

async def generate_resolution(text: str) -> str:
    prompt = f"꿈 꿨는데 이 꿈을 짧게 해몽 해줘. 내용을 사람처럼 말해주고 첫 문장은 '이 꿈은' 으로 시작해줘. langth=150, 문단 변경없이 해몽 내용만 반환해줘. 꿈 내용 : {text}"
    dream_resolution = await send_bard_request(prompt)
    return dream_resolution

async def generate_resolution_mvp(text: str) -> str:
    prompt = f"꿈 꿨는데 이 꿈을 짧게 해몽 해줘. 내용을 사람처럼 말해주고 첫 문장은 '이 꿈은' 으로 시작해줘. langth=150, 문단 변경없이 해몽 내용만 반환해줘. 꿈 내용 : {text}"
    dream_resolution = await send_bard_request(prompt)
    return dream_resolution
