from pydantic import BaseModel

class Generate(BaseModel):
    text: str
class Image(BaseModel):
    textId: int
class Resolution(BaseModel):
    text: str
