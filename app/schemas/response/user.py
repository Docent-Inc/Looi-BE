from pydantic import BaseModel
class User(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool

    class Config:
        orm_mode = True