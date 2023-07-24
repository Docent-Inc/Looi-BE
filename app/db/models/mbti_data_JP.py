from sqlalchemy import Column, Integer, Text
from app.db.models.line_chatbot_dream import get_Base

Base = get_Base()

class Mbti_data_JP(Base):
    __tablename__ = "MBTI_data_JP"

    id = Column(Integer, primary_key=True)
    user_text = Column(Text, nullable=False)
    mbti_resolution = Column(Text, nullable=False)
def get_Base():
    return Base
