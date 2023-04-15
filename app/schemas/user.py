from pydantic import BaseModel
'''
회원가입 request body 구조
'''
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

