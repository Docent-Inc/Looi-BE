from pydantic import BaseModel

class BasicResponse(BaseModel):
    id: int
    dream_name: str
    dream: str
    image_url: str

class ImageResponse(BaseModel):
    image_url: str

class CheckListResponse(BaseModel):
    today_checklist: str
class ResolutionResponse(BaseModel):
    dream_resolution: str