from pydantic import BaseModel

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