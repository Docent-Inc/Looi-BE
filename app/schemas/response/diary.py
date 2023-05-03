from pydantic import BaseModel

class DiaryResponse(BaseModel):
    is_public: bool
    is_owner: bool
    dream_name: str
    dream: str
    image_url: str
    create_date: str
    modified_date: str
    view_count: int
    like_count: int
    is_modified: bool

class DiaryListResponse(BaseModel):
    id: int
    dream_name: str
    image_url: str
    view_count: int
    like_count: int
    comment_count: int