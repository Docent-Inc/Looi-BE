from sqlalchemy import Column, Integer
from app.db.models.mbti_data import get_MBTIBase

Base = get_MBTIBase()

class kakao_chatbot_user(Base):
    __tablename__ = "kakao_chatbot_user"

    id = Column(Integer, primary_key=True)
    kakao_user_id = Column(Integer, nullable=False)
    day_count = Column(Integer, nullable=False)
    total_generated_dream = Column(Integer, nullable=False)

def get_kakao_chatbot_userBase():
    return Base
