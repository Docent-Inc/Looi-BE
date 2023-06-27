from sqlalchemy import Column, Integer, ForeignKey, Text
from app.db.models.search import get_SearchHistoryBase

Base = get_SearchHistoryBase()

class Diary_ko(Base):
    __tablename__ = "Diary_KR"

    id = Column(Integer, primary_key=True)
    Diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    dream_name = Column(Text, nullable=False)
    dream = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)

def get_Diary_koBase():
    return Base