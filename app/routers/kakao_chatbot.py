import asyncio
from typing import Optional, List, Dict, Any

import requests
from fastapi import APIRouter, Depends
from pydantic import BaseModel, root_validator, ValidationError
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from app.db.database import get_db
from app.feature.diary import createDiary
from app.feature.generate_kr import generate_text, generate_resolution
from app.schemas.request.crud import Create

router = APIRouter(prefix="/kakao-chatbot")

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


class SimpleImage(BaseModel):
    imageUrl: str

class Output(BaseModel):
    simpleImage: Optional[SimpleImage] = None
    simpleText: Optional[SimpleText] = None

    @root_validator
    def check_fields(cls, values):
        simpleImage, simpleText = values.get('simpleImage'), values.get('simpleText')
        if simpleImage is None and simpleText is None:
            raise ValidationError('Either simpleImage or simpleText field must be set')
        return values


async def create_callback_request_kakao(prompt: str, url: str, db: Session) -> dict:
    try:
        # 꿈 그리기
        # 해몽
        print(1)
        task1, task2 = await asyncio.gather(
            generate_text(prompt, 2, db),
            generate_resolution(prompt)
        )
        print(2)

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

        request_body = KakaoChatbotResponse(
            version="2.0", template=Template(outputs=[
                Output(simpleImage=SimpleImage(imageUrl=dream_image_url)),
                Output(simpleText=SimpleText(text=f"꿈 이름: {dream_name}\n꿈 내용: {dream}\n해몽: {dream_resolution}"))
            ])).dict()

        if request_body.status_code == 200:
            return {"status": "success"}

        return {"status": "fail"}

    except Exception as e:
        print(e)
        return {"error": e}



@router.post("/api/chat/callback", tags=["kakao"], response_model=KakaoChatbotResponseCallback)
async def make_chatgpt_async_callback_request_to_openai_from_kakao(
        kakao_ai_request: KakaoAIChatbotRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
):

    background_tasks.add_task(create_callback_request_kakao,
                              prompt=kakao_ai_request.userRequest.utterance, url=kakao_ai_request.userRequest.callbackUrl, db=db)
    return KakaoChatbotResponseCallback(version="2.0", useCallback=True)
