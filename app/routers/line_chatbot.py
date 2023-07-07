from aiohttp import ClientTimeout
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, ImageMessage
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.database import get_SessionLocal
from app.feature.diary import createDiary
from app.feature.generate_jp import generate_text, generate_resolution_linechatbot
from app.schemas.common import ApiResponse
from app.schemas.request.crud import Create
from linebotx import LineBotApiAsync, WebhookHandlerAsync
from linebotx.http_client import AioHttpClient, AioHttpResponse
from pytz import timezone

scheduler = AsyncIOScheduler(timezone="Asia/Tokyo")
user_requests = {}
MAX_REQUESTS_PER_DAY = 3  # This can be any number you want
# Define the function to reset the counter
def reset_counter():
    global user_requests
    user_requests = {}

# Schedule the function to run every day at midnight
scheduler.add_job(reset_counter, 'cron', hour=0)
scheduler.start()
load_dotenv()



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
    dream_text = event.message.text
    SessionLocal = get_SessionLocal()
    db = SessionLocal()  # 실제 데이터베이스 세션을 얻는다.
    try:
        # 글자 수 제한
        if len(dream_text) < 10 or len(dream_text) > 200:
            await line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="10文字以上200文字以下で入力してください。"))  # Echo message
            return

        # 꿈 생성 제한 3회
        user_id = event.source.user_id
        if user_id not in user_requests:
            user_requests[user_id] = 0
        if user_requests[user_id] > MAX_REQUESTS_PER_DAY:
            await line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="1日3回までです。"))
            return

        # 꿈 생성
        id, dream_name, dream, dreCam_image_url = await generate_text(dream_text, 3, db)
        # 해몽 생성
        dream_resolution = await generate_resolution_linechatbot(dream_text)

        create = Create(
            dream_name=dream_name,
            dream=dream,
            image_url=dream_image_url,
            resolution=dream_resolution,
            checklist="checklist",
            is_public=True,
        )

        await createDiary(create, 3, db)
        generated_text = f"【{dream_name}】\n{dream}\n\n【夢占い】\n{dream_resolution}"
        user_requests[user_id] += 1
        await line_bot_api.reply_message(
            event.reply_token,
            [ImageSendMessage(original_content_url=dream_image_url, preview_image_url=dream_image_url),
             TextSendMessage(text=generated_text)]
        )

        return
    finally:
        db.close()
