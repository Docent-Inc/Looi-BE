from typing import Optional, Union

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
    nickname: Optional[str] = ""
    mbti: Optional[str] = ""
    gender: Optional[str] = ""
    birth: Optional[str] = ""
    push_token: Optional[str] = ""

class PushUpdateRequest(BaseModel):
    type: str
    value: Union[bool, int]

'''
Diary 관련 Request
'''

class CreateDreamRequest(BaseModel):
    content: str

class UpdateDreamRequest(BaseModel):
    diary_name: Optional[str] = ""
    content: Optional[str] = ""

class CreateDiaryRequest(BaseModel):
    date: Optional[str] = ""
    diary_name: Optional[str] = ""
    content: str
class UpdateDiaryRequest(BaseModel):
    date: Optional[str] = ""
    diary_name: Optional[str] = ""
    content: Optional[str] = ""

class CreateMemoRequest(BaseModel):
    title: Optional[str] = ""
    content: str

class UpdateMemoRequest(BaseModel):
    title: Optional[str] = ""
    content: Optional[str] = ""

class CreateCalendarRequest(BaseModel):
    start_time: Optional[str] = ""
    end_time: Optional[str] = ""
    title: Optional[str] = ""
    content: str

class UpdateCalendarRequest(BaseModel):
    start_time: Optional[str] = ""
    end_time: Optional[str] = ""
    title: Optional[str] = ""
    content: Optional[str] = ""

class ListCalendarRequest(BaseModel):
    year: int
    month: int
    day: Optional[int] = 0




class ChatRequest(BaseModel):
    type: Optional[int] = 0
    content: str

class WelcomeRequest(BaseModel):
    text: str
    type: int

class HelperRequest(WelcomeRequest):
    pass