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
    age: str
    gender: str


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
    start_date: str
    end_date: str
    title: str
    content: str