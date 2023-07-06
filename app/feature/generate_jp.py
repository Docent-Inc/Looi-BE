import asyncio
from app.core.current_time import get_current_time
from app.feature.gptapi.generateImg import generate_img
from app.db.models.dream import DreamText, DreamImage
from app.db.database import get_db
from app.feature.gptapi.gptRequset import send_gpt_request, send_bard_request


async def generate_text(text: str, userId: int, db: get_db()) -> str:
    async def get_dreamName(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "夢の内容を理解し、あなたが面白い夢のタイトルを作ってください"},
            {"role": "system", "content": "日本語で書くだけ"},
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

async def generate_resolution_linechatbot(text: str) -> str:
    prompt = f"夢を見ましたが、この夢を短く解釈してください。人間のように話し、最初の文章は'この夢は'と始まってください。length=150、段落の変更なしで解釈内容だけを返してください。夢の内容：{text}"
    dream_resolution = await send_bard_request(prompt)
    return dream_resolution