from pydantic import BaseModel
class Create(BaseModel):
    dream_name: str
    dream: str
    image_url: str
