from pydantic import BaseModel

class TokenData(BaseModel):
    access_token: str
    expires_in: int
    token_type: str


class TokenDataInfo(TokenData):
    refresh_token: str
    refresh_expires_in: int
    user_email: str
    user_password: str
    user_nickname: str