import asyncio

from fastapi import HTTPException
from starlette import status

from app.core.current_time import get_current_time
from app.feature.gptapi.generateImg import generate_img, get_text_data
from app.db.models.dream import DreamText, DreamImage, DreamResolution
from app.db.database import get_db
from app.feature.gptapi.gptRequset import send_gpt_request

async def generate_text(text: str, userId: int, db: get_db()) -> str:
    async def get_dreamName(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "꿈의 내용을 이해하고 너가 재미있는 꿈의 제목을 만들어줘"},
            {"role": "user", "content": message}
        ]
        dreamName = await send_gpt_request(messages_prompt)
        return dreamName

    async def DALLE2(message: str):
        try:
            messages_prompt = [
                {"role": "system", "content": "Understand this dream and make just one scene a prompt for DALLE2, include the word illustration"},
                {"role": "system", "content": "make just prompt only engilsh"},
                {"role": "system", "content": "max_length=100"},
                {"role": "user", "content": message}
            ]
            prompt = await send_gpt_request(messages_prompt)
        except Exception as e:
            return str(e)
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

async def generate_resolution(TextId: int, user_id: int, db: get_db()) -> str:
    async def get_dream_resolution(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "이 꿈을 공손하게 재미요소를 담아서 해몽해줘"},
            {"role": "system", "content": "max_length=60"},
            {"role": "user", "content": message}
        ]
        response = await send_gpt_request(messages_prompt)
        return response

    # 데이터베이스에서 textId와 current_user.id를 확인 후 dream 가져오기
    text_data = await get_text_data(TextId, user_id, db)
    if text_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="생성된 꿈이 없습니다.")

    dream = text_data.dream  # 생성된 꿈 정보 불러오기

    dream_resolution = await get_dream_resolution(dream)
    return dream_resolution

async def generate_checklist(resolution: str, TextId: int, db: get_db()) -> str:
    async def get_today_checklist(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "이 꿈의 해몽을 바탕으로 현실에서 오늘 하루의 체크리스트 조금 자세하게 3개 만들어줘"},
            {"role": "system", "content": "~해보기, ~하기 와 같은 말투로 제목없이, 1. 2. 3. 으로 나열해주고, 줄바꿈은 한번씩만 해줘"},
            {"role": "system", "content": "max_length=60"},
            {"role": "user", "content": message},
        ]
        response = await send_gpt_request(messages_prompt)
        return response

    check_list = await get_today_checklist(resolution)

    try:
        data = DreamResolution(
            Text_id=TextId,
            dream_resolution=resolution,
            today_checklist=check_list
        )
        db.add(data)
        db.commit()
        db.refresh(data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return check_list

async def generate_resolution_mvp(text: str) -> str:
    async def get_dream_resolution(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "이 꿈을 공손하게 재미요소를 담아서 해몽하고 내용만 보내줘"},
            {"role": "system", "content": "max_length=60"},
            {"role": "user", "content": message}
        ]
        response = await send_gpt_request(messages_prompt)
        return response

    dream_resolution = await get_dream_resolution(text)
    return dream_resolution
