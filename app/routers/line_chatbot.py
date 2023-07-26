import aiocron
import pytz
from aiohttp import ClientTimeout
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, ImageMessage
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List
import os
from app.db.database import get_SessionLocal
from app.db.models.line_chatbot_dream import line_chatbot_dream
from app.db.models.line_chatbot_user import line_chatbot_user
from app.feature.diary import createDiary
from app.feature.generate_jp import generate_text, generate_resolution_clova
from app.schemas.common import ApiResponse
from app.schemas.request.crud import Create
from linebotx import LineBotApiAsync, WebhookHandlerAsync
from linebotx.http_client import AioHttpClient, AioHttpResponse
from pytz import timezone
# 매일 0시에 모든 user 의 day_count 를 0으로 초기화
MAX_REQUESTS_PER_DAY = 3
async def reset_day_count():
    SessionLocal = get_SessionLocal()
    db = SessionLocal()
    try:
        users = db.query(line_chatbot_user).all()
        for user in users:
            user.day_count = 0
        db.commit()
        print("Reset line day_count successfully")
    finally:
        db.close()

# Schedule the reset_day_count function to run at 0:00 every day (KST)
cron_task = aiocron.crontab('0 0 * * *', func=reset_day_count, tz=pytz.timezone('Asia/Tokyo'))


mbti_list = [
        "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ",
        "ENFJ", "ENTJ",
        "istj", "isfj", "infj", "intj", "istp", "isfp", "infp", "intp", "estp", "esfp", "enfp", "entp", "estj", "esfj",
        "enfj", "entj",
        "Istj", "Isfj", "Infj", "Intj", "Istp", "Isfp", "Infp", "Intp", "Estp", "Esfp", "Enfp", "Entp", "Estj", "Esfj",
        "Enfj", "Entj",
    ]

class CustomAioHttpClient(AioHttpClient):
    def __init__(self):
        self.timeout = ClientTimeout(total=300)
        super().__init__()

    async def post(self, url, headers=None, data=None, timeout=None):
        timeout = timeout or self.timeout
        async with self.session.post(url, headers=headers, data=data, timeout=timeout) as response:
            return AioHttpResponse(response)

    async def put(self, url, headers=None, data=None, timeout=None):
        async with self.session.put(url, headers=headers, data=data, timeout=timeout) as response:
            return AioHttpResponse(response)


# Use the custom http client
line_bot_api = LineBotApiAsync(os.getenv("LINE_ACCESS_TOKEN"), http_client=CustomAioHttpClient())
handler = WebhookHandlerAsync(os.getenv("LINE_SECRET"))

class LineEvent(BaseModel):
    replyToken: str
    type: str
    mode: str
    timestamp: int
    source: dict
    message: dict

class LineWebhookBody(BaseModel):
    destination: str
    events: List[LineEvent]

router = APIRouter(prefix="/chatbot")

@router.post("/callback", tags=["LineChatbot"])
async def callback(request: Request):
    body = await request.body()
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        print("Signature is missing.")
        raise HTTPException(status_code=400, detail="Bad Request: Signature is missing.")
    try:
        await handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature. Check your channel access token/channel secret.")
    return ApiResponse(
        success=True
    )

@handler.add(MessageEvent, message=TextMessage)
async def handle_message(event):
    '''
    Line 챗봇 메시지 핸들러

    :param event: 라인에서 보내주는 사용자 정보 body
    :return:
    '''
    dream_text = event.message.text
    SessionLocal = get_SessionLocal()
    db = SessionLocal()  # 실제 데이터베이스 세션을 얻는다.
    try:
        # user_id는 라인 챗봇 사용자의 고유 식별자입니다.
        user_id = event.source.user_id

        # database에 저장된 사용자의 정보를 가져옵니다.
        user = db.query(line_chatbot_user).filter(line_chatbot_user.line_user_id == user_id).first()
        if user is None:
            user = line_chatbot_user(
                line_user_id=user_id,
                day_count=0,
                total_generated_dream=0,
            )
            db.add(user)
            db.commit()

        # mbti설정
        if dream_text in mbti_list:
            user.mbti = dream_text
            db.commit()
            await line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="MBTIが設定されました。"))
            return
        # 도움말
        elif dream_text == "おしえて":
            await line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="「夢」を入力すると夢を作成します。"))
            return
        # 내 정보
        elif dream_text == "じこ":
            if user.mbti is None:
                await line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="まだMBTIが設定されていません。" + "\n" + "MBTIを設定すると夢の解釈ができます。" + "\n" + "今日生成可能な夢の数:" + str( MAX_REQUESTS_PER_DAY - user.day_count) + "回" + "\n" + "総生成した夢の数: " + str(user.total_generated_dream) + "回"))
                return
            else:
                await line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="MBTI: " + user.mbti + "\n" + "今日生成可能な夢の数:" + str( MAX_REQUESTS_PER_DAY - user.day_count) + "回" + "\n" + "総生成した夢の数: " + str(user.total_generated_dream) + "回"))
                return

        # 글자 수 제한
        elif len(dream_text) < 10 or len(dream_text) > 200:
            await line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="10文字以上200文字以下で入力してください。"))  # Echo message
            return

        # 꿈 생성 제한 3회
        if user.day_count >= MAX_REQUESTS_PER_DAY:
            await line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="1日3回までです。"))
            return

        # 꿈 생성
        id, dream_name, dream, dream_image_url = await generate_text(dream_text, 3, db)
        # 해몽 생성
        if user.mbti is None:
            dream_resolution = await generate_resolution_clova(dream_text, db)
        else:
            dream_resolution = await generate_resolution_clova(user.mbti + ", " + dream_text, db)

        create = Create(
            dream_name=dream_name,
            dream=dream,
            image_url=dream_image_url,
            resolution=dream_resolution,
            checklist="checklist",
            is_public=True,
        )

        diary_id = await createDiary(create, 3, db)
        generated_text = f"{dream_name}\n\n{dream}\n\n夢占い: {dream_resolution}"
        await line_bot_api.reply_message(
            event.reply_token,
            [ImageSendMessage(original_content_url=dream_image_url, preview_image_url=dream_image_url),
             TextSendMessage(text=generated_text)]
        )

        user_id = user.id
        line_user_dream = line_chatbot_dream(
            user_id=user_id,
            diary_id=diary_id,
        )
        db.add(line_user_dream)
        db.commit()

        user = db.query(line_chatbot_user).filter(line_chatbot_user.id == user_id).first()
        user.day_count += 1
        user.total_generated_dream += 1
        db.commit()

        return
    finally:
        db.close()
