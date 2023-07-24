from sqlalchemy import Column, Integer, Text
from app.db.models.diary_jp import get_Diary_jpBase

Base = get_Diary_jpBase()

class Mbti_data_KR(Base):
    __tablename__ = "MBTI_data_KR"

    id = Column(Integer, primary_key=True)
    user_text = Column(Text, nullable=False)
    mbti_resolution = Column(Text, nullable=False)
def get_Base():
    return Base
