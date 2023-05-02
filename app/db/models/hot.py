from sqlalchemy import Column, Integer, ForeignKey
from app.db.models.like import get_LikeBase
Base = get_LikeBase()

class Hot(Base):
    __tablename__ = "Hot"

    id = Column(Integer, primary_key=True)
    index = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    Diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)

def get_HotBase():
    return Base
