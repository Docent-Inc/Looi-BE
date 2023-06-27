from sqlalchemy import Column, Integer, ForeignKey, Text
from app.db.models.diary_ko import get_Diary_koBase

Base = get_Diary_koBase()

class Diary_en(Base):
    __tablename__ = "Diary_EN"

    id = Column(Integer, primary_key=True)
    Diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    dream_name = Column(Text, nullable=False)
    dream = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)

def get_Diary_enBase():
    return Base