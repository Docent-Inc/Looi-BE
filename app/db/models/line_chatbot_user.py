from sqlalchemy import Column, Integer, String, Text
from app.db.models.kakao_chatbot_dream import get_Base

Base = get_Base()

class line_chatbot_user(Base):
    __tablename__ = "line_chatbot_user"

    id = Column(Integer, primary_key=True)
    line_user_id = Column(Text, nullable=False)
    mbti = Column(String(4), nullable=True)
    day_count = Column(Integer, nullable=False)
    total_generated_dream = Column(Integer, nullable=False)

def get_Base():
    return Base