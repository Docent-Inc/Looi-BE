from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean
from app.db.models.user import get_UserBase

Base = get_UserBase()

class DreamText(Base):
    __tablename__ = "DreamText"

    id = Column(Integer, primary_key=True)
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    User_text = Column(Text, nullable=False)
    dream_name = Column(Text, nullable=False)
    dream = Column(Text, nullable=False)
    DALLE2 = Column(Text, nullable=False)
    date = Column(String(14), nullable=False)
    is_deleted = Column(Boolean, default=False)

class DreamImage(Base):
    __tablename__ = "DreamImage"

    id = Column(Integer, primary_key=True)
    Text_id = Column(Integer, ForeignKey('DreamText.id'), nullable=False)
    dream_image_url = Column(String(100), nullable=False)

def get_DreamBase():
    return Base
