from typing import Optional

from pydantic import BaseModel

'''
Auth 관련 Response
'''
class TokenData(BaseModel):
    access_token: str
    expires_in: int
    token_type: str
class TokenDataInfo(TokenData):
    refresh_token: str
    refresh_expires_in: int
    user_email: str
    user_password: str
    user_nickname: str

class User(BaseModel):
    id: int
    nickname: str
    email: str
    mbti: str

    class Config:
        orm_mode = True

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

class KakaoChatbotResponse(BaseModel):
    version: str
    template: Template