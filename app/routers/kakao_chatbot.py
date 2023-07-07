import asyncio
from typing import Optional, List, Dict, Any

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends
from pydantic import BaseModel, root_validator, ValidationError
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from app.db.database import get_db
from app.feature.diary import createDiary
from app.feature.generate_kr import generate_text, generate_resolution
from app.schemas.request.crud import Create

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
user_requests = {}
MAX_REQUESTS_PER_DAY = 3  # This can be any number you want
# Define the function to reset the counter
def reset_counter():
    global user_requests
    user_requests = {}

# Schedule the function to run every day at midnight
scheduler.add_job(reset_counter, 'cron', hour=0)
scheduler.start()

router = APIRouter(prefix="/kakao-chatbot")


class SimpleImage(BaseModel):
    imageUrl: str


class SimpleText(BaseModel):
    text: str


class Output(BaseModel):
    simpleImage: Optional[SimpleImage] = None
    simpleText: Optional[SimpleText] = None



class Template(BaseModel):
    outputs: list[Output]


class KakaoChatbotResponseCallback(BaseModel):
    version: str
    useCallback: bool

class Bot(BaseModel):
    id: str
    name: str


class Reason(BaseModel):
    code: int
    message: str


class Extra(BaseModel):
    reason: Reason


class Intent(BaseModel):
    id: str
    name: str
    extra: Extra


class Action(BaseModel):
    id: str
    name: str
    params: Dict[str, Any]
    detailParams: Dict[str, Any]
    clientExtra: Dict[str, Any]


class Block(BaseModel):
    id: str
    name: str


class Properties(BaseModel):
    botUserKey: str
    plusfriendUserKey: str
    bot_user_key: str
    plusfriend_user_key: str


class User(BaseModel):
    id: str
    type: str
    properties: Properties


class Params(BaseModel):
    surface: str


class UserRequest(BaseModel):
    block: Block
    user: User
    utterance: str
    params: Params
    callbackUrl: str
    lang: str
    timezone: str


class KakaoAIChatbotRequest(BaseModel):
    bot: Optional[Bot] = None
    intent: Optional[Intent] = None
    action: Optional[Action] = None
    userRequest: Optional[UserRequest] = None
    contexts: Optional[List] = None


class KakaoChatbotResponse(BaseModel):
    version: str
    template: Template
async def create_callback_request_kakao(prompt: str, url: str, db: Session) -> dict:
    try:
        task1, task2 = await asyncio.gather(
            generate_text(prompt, 2, db),
            generate_resolution(prompt)
        )

        id, dream_name, dream, dream_image_url = task1
        dream_resolution = task2

        create = Create(
            dream_name=dream_name,
            dream=dream,
            image_url=dream_image_url,
            resolution=dream_resolution,
            checklist="checklist",
            is_public=True,
        )
        await createDiary(create, 2, db)

        outputs = [
            Output(simpleImage=SimpleImage(imageUrl=dream_image_url)),
            Output(simpleText=SimpleText(text=f"{dream_name}\n\n꿈 내용: {dream}\n\n해몽: {dream_resolution}"))
        ]

        request_body = KakaoChatbotResponse(
            version="2.0",
            template=Template(outputs=outputs)
        ).dict()

        response = requests.post(url, json=request_body)

        if response.status_code == 200:
            print("success")
        else:
            print(response.status_code)
            print(response.text)

    except Exception as e:
        print(e)
        return {"error": e}



@router.post("/api/chat/callback", tags=["kakao"], response_model=KakaoChatbotResponseCallback)
async def make_chatgpt_async_callback_request_to_openai_from_kakao(
        kakao_ai_request: KakaoAIChatbotRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
):
    # Userid로 카운트를 해서 한국시간 기준 12시에 초기화
    # 총 3회까지 가능함
    # 코드 만들어줘
    # 꿈 생성 제한 3회
    user_id = kakao_ai_request.user.id
    if user_id not in user_requests:
        user_requests[user_id] = 0
    if user_requests[user_id] > MAX_REQUESTS_PER_DAY:
        return KakaoChatbotResponse(version="2.0", template={"outputs": [{"simpleText": {"text": "꿈 분석은 하루에 3번만 가능해요ㅠㅠ 내일 다시 시도해주세요"}}]})


    background_tasks.add_task(create_callback_request_kakao,
                              prompt=kakao_ai_request.userRequest.utterance, url=kakao_ai_request.userRequest.callbackUrl, db=db)

    user_requests[user_id] += 1
    return KakaoChatbotResponseCallback(version="2.0", useCallback=True)
