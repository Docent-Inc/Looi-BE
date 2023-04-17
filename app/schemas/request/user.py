from typing import Optional
from pydantic import BaseModel


class UserBase(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    nickName: Optional[str] = None  # Add this line


class UserCreate(UserBase):
    email: str
    username: str
    password: str
    nickName: str  # Add this line

