from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os

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

@router.post("/callback")
async def callback(request: Request, body: Optional[LineWebhookBody] = None):
    signature = request.headers['X-Line-Signature']
    handler.handle(body.json(), signature)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))  # Echo message

