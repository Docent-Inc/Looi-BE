import asyncio
from app.core.current_time import get_current_time
from app.feature.generateImg import generate_img
from app.db.models.dream import DreamText, DreamImage
from app.db.database import get_db
from app.feature.aiRequset import send_gpt_request, send_bard_request, send_hyperclova_request
from translate import Translator

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
            {"role": "system", "content": "make just one scene a prompt for DALLE2 about this dream"},
            {"role": "system", "content": "include the word illustration and 7 world about Subject, Medium, Environment, Lighting, Color, Mood, Compoition"},
            {"role": "system", "content": "make just prompt only engilsh"},
            {"role": "system", "content": "max_length=200"},
            {"role": "user", "content": "運転中に事故が発生しましたが、痛すぎました。"},
            {"role": "system", "content": "A digital art illustration vividly depicting a car accident on a bustling city street, bathed in harsh daylight that intensifies the vibrant and contrasting colors, the intense and painful mood is centralized on the moment of collision."},
            {"role": "user", "content": "運転中に事故が発生しましたが、痛すぎました。"},
            {"role": "system", "content": "A terrifying digital illustration of a dark, foreboding scene where an unseen antagonist's hands are tightly wrapped around the dreamer's throat, a stark contrast of vivid red blood against the dreamer's pallid skin, symbolizing imminent death."},
            {"role": "user", "content": message}
        ]
        prompt = await send_gpt_request(messages_prompt)

        dream_image_url = await generate_img(1, prompt, userId, db)
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

async def generate_resolution_clova(text: str, db: get_db()) -> str:
    prompt = f"꿈을 요소별로 자세하게, mbti맞춤 해몽 해줘. mbti가 입력되지 않았으면 자세하게 꿈의 요소별 일반적인 꿈 해몽 해줘." \
             f"###꿈 내용: {text}"
    # HyperClova를 호출하여 해몽 결과물을 받아옴
    dream_resolution = await send_hyperclova_request(prompt)
    dream_resolution = dream_resolution.replace("###클로바:", "").lstrip()

    # 한국어를 일본어로 번역
    translator = Translator(to_lang="ja")
    dream_resolution = translator.translate(dream_resolution)

    return dream_resolution