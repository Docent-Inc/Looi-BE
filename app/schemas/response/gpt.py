from pydantic import BaseModel

'''
bmongsmong.com
pretotyping 설문조사 페이지 response 구조
'''
class BasicResponse(BaseModel):
    dream_name: str
    dream: str
    image_url: str

class ImageResponse(BaseModel):
    image_url: str

class CheckListResponse(BaseModel):
    dream_resolution: str
    today_checklist: str