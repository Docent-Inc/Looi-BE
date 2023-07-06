import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
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
    if body is None:
        print("Request body is missing.")
        raise HTTPException(status_code=400, detail="Bad Request: Request body is missing.")
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        print("Signature is missing.")
        raise HTTPException(status_code=400, detail="Bad Request: Signature is missing.")
    try:
        print(body.json())
        handler.handle(body.json(), signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature. Check your channel access token/channel secret.")
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))  # Echo message

