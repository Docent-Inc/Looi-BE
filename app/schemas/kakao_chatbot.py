from typing import Optional, List, Dict, Any
from pydantic import BaseModel

'''
카카오 챗봇을 위한 API 스키마
'''

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
    useCallback: Optional[bool] = None
    template: Optional[Template] = None

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