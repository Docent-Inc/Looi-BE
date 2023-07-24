from sqlalchemy import Column, Integer, Text
from app.db.models.mbti_data_JP import get_Base

Base = get_Base()

class today_luck(Base):
    __tablename__ = "today_luck"

    id = Column(Integer, primary_key=True)
    user_text = Column(Text, nullable=False)
    today_luck = Column(Text, nullable=False)
def get_Base():
    return Base