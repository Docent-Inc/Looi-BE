from sqlalchemy import Column, Integer, ForeignKey, Text
from app.db.models.diary_en import get_Diary_enBase

Base = get_Diary_enBase()

class Diary_jp(Base):
    __tablename__ = "Diary_JP"

    id = Column(Integer, primary_key=True)
    Diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    dream_name = Column(Text, nullable=False)
    dream = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)

def get_Diary_jpBase():
    return Base