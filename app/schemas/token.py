from pydantic import BaseModel

'''
jwt 토큰 response 구조
'''
class TokenData(BaseModel):
    access_token: str
    token_type: str


