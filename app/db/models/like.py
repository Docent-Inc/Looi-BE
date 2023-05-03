from sqlalchemy import Column, Integer, ForeignKey
from app.db.models.diary import get_DiaryBase
Base = get_DiaryBase()

class Like(Base):
    __tablename__ = "Like"

    id = Column(Integer, primary_key=True)
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    Diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)

def get_LikeBase():
    return Base