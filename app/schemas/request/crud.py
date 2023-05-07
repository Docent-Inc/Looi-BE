from pydantic import BaseModel
class Create(BaseModel):
    dream_name: str
    dream: str
    image_url: str
    resolution: str
    checklist: str
    is_public: bool

class Update(BaseModel):
    dream_name: str
    dream: str

class commentRequest(BaseModel):
    comment: str