from pydantic import BaseModel

class DiaryBase(BaseModel):
    is_public: bool
    date: str
    image_url: str
    view_count: int
    like_count: int

class DiaryPublic(DiaryBase):
    dream_name: str
    dream: str
    is_owner: bool

class DiaryOwner(DiaryPublic):
    pass