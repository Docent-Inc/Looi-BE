from pydantic import BaseModel

class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_email: str
    user_password: str
    user_nickname: str
