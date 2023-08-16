from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    nickName: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class NicknameChangeRequest(BaseModel):
    nickName: str

class KakaoLoginRequest(BaseModel):
    code: str