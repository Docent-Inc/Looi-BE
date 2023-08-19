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


'''
Diary 관련 Response
'''
class CreateDiaryRequest(BaseModel):
    image_model: int
    content: str