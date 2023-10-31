from typing import Optional

from pydantic import BaseModel

'''
Auth 관련 Request
'''
class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
class NicknameChangeRequest(BaseModel):
    nickname: str
class KakaoLoginRequest(BaseModel):
    code: str
class MbtiChangeRequest(BaseModel):
    mbti: str
class TokenRefresh(BaseModel):
    refresh_token: str

class UserUpdateRequest(BaseModel):
    nickname: str
    mbti: str
    gender: str
    birth: str

class PushUpdateRequest(BaseModel):
    type: str
    value: bool


'''
Diary 관련 Response
'''
class CreateDiaryRequest(BaseModel):
    content: str

class UpdateDiaryRequest(BaseModel):
    diary_name: str
    diary_content: str

class MemoRequest(BaseModel):
    content: str

class ChatRequest(BaseModel):
    content: str

class CalenderRequest(BaseModel):
    start_time: str
    end_time: str
    title: str
    content: str

class ListRequest(BaseModel):
    page: int
    diary_type: int

class CalenderListRequest(BaseModel):
    year: int
    month: int
    day: Optional[int] = None

class WelcomeRequest(BaseModel):
    text: str
    type: int

class HelperRequest(WelcomeRequest):
    pass