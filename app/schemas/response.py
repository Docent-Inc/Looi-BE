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

class ChatResponse(BaseModel):
    calls_left: int
    text_type: int
    diary_id: int
    content: object