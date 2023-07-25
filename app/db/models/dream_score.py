from sqlalchemy import Column, Integer, ForeignKey
from app.db.models.today_luck import get_Base

Base = get_Base()

class dream_score(Base):
    __tablename__ = "dream_score"

    id = Column(Integer, primary_key=True)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    score = Column(Integer, nullable=False)
def get_Base():
    return Base