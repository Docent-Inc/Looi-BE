from pydantic import BaseModel

class DiaryResponse(BaseModel):
    is_public: bool
    is_owner: bool
    dream_name: str
    dream: str
    image_url: str
    date: str
    view_count: int
    like_count: int