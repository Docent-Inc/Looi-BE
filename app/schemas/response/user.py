from pydantic import BaseModel
class User(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool

    class Config:
        orm_mode = True

class PasswordChangeResponse(BaseModel):
    message: str

class NicknameChangeResponse(BaseModel):
    message: str
class DeleteUserResponse(BaseModel):
    message: str
class SignupResponse(BaseModel):
    message: str