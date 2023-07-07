import asyncio
import logging
from typing import Optional, List, Dict, Any

import requests
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from app.db.database import get_db
from app.feature.diary import createDiary
from app.feature.generate_kr import generate_text, generate_resolution
from app.schemas.request.crud import Create

router = APIRouter(prefix="/kakao-chatbot")

# @router.post("/api/chat", tags=["kakao"], response_model=KakaoChatbotResponse)
# async def make_chatgpt_request_to_openai_from_kakao(completion_request: KakaoChatbotRequest):
#     completion = await create_completion_request(prompt=completion_request.userRequest.utterance)
#     # erase newline
#     completion = completion.strip()
#     template = {
#         "outputs": [
#             {"simpleText": {"text": completion}}
#         ]
#     }
#     return KakaoChatbotResponse(version="2.0", template=template)


class SimpleText(BaseModel):
    text: str


class Output(BaseModel):
    simpleText: SimpleText


class Template(BaseModel):
    outputs: list[Output]


class KakaoChatbotResponse(BaseModel):
    version: str
    template: Template


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

async def create_callback_request_kakao(prompt: str, url: str, db: Session) -> dict:
    try:
        # 꿈 그리기
        # 해몽
        task1, task2 = await asyncio.gather(
            generate_text(prompt),
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

        template = {
            "outputs": [
                {"simpleText": {"text": f"꿈 이름: {dream_name}\n꿈 내용: {dream}\n해몽: {dream_resolution}"}},
                {"simpleImage": {"imageUrl": dream_image_url}}
            ]
        }

        return template

        # request_body = KakaoChatbotResponse(
        #     version="2.0", template=template).dict()
        # res = requests.post(url, json=request_body)
        #
        # if not res.ok:
        #     logging.error(f"[ERROR] Kakao POST {url} failed.")
        #
        # print(f"sent request to kakao POST {url}, Code: {res.status_code}")
    except Exception as e:
        return {"error": e}


@router.post("/api/chat/callback", tags=["kakao"], response_model=KakaoChatbotResponseCallback)
async def make_chatgpt_async_callback_request_to_openai_from_kakao(
        kakao_ai_request: KakaoAIChatbotRequest,
        db: Session = Depends(get_db),
):
    # background_tasks.add_task(create_callback_request_kakao,
    #                           prompt=kakao_ai_request.userRequest.utterance, url=kakao_ai_request.userRequest.callbackUrl, db=db)
    template = await create_callback_request_kakao(kakao_ai_request.userRequest.utterance, kakao_ai_request.userRequest.callbackUrl, db)
    return KakaoChatbotResponseCallback(version="2.0", template=template)
