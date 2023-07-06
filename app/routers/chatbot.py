from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, ImageMessage
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app import db
from app.feature.diary import createDiary
from app.feature.generate_jp import generate_text, generate_resolution_linechatbot
from app.schemas.request.crud import Create

# Initialize the scheduler
scheduler = AsyncIOScheduler()
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

line_bot_api = LineBotApi(os.getenv("LINE_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_SECRET"))

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

