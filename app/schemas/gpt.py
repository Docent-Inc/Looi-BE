from pydantic import BaseModel
class GPTResponse(BaseModel):
    dream_name: str
    dream: str
    dream_resolution: str
    today_luck: str
    image_url: str