from pydantic import BaseModel

class Generate(BaseModel):
    image_model: int
    text: str
class ImageRequest(BaseModel):
    image_model: int
    text: str
class Resolution(BaseModel):
    text: str
