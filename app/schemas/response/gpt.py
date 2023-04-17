from pydantic import BaseModel

'''
bmongsmong.com
pretotyping 설문조사 페이지 response 구조
'''
class BasicResponse(BaseModel):
    dream_name: str
    dream: str
    dream_resolution: str
    today_luck: str
    image_url: str

class ImageResponse(BaseModel):
    image_url: str