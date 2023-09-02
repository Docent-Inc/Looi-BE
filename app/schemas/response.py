from typing import Optional, Any

from pydantic import BaseModel

class ApiResponse(BaseModel):
    success: bool = True
    status_code: Optional[int] = 2000
    message: Optional[str] = "요청이 성공적으로 처리되었습니다."
    data: Optional[Any] = None

'''
Auth 관련 Response
'''
class TokenData(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    token_type: str

class KakaoTokenData(TokenData):
    is_signup: bool
    user_name: str

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