from pydantic import BaseModel

class Generate(BaseModel):
    image_model: int
    text: str
class Image(BaseModel):
    image_model: int
    textId: int
class Resolution(BaseModel):
    text: str
