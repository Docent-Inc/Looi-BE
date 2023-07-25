from sqlalchemy import Column, Integer, ForeignKey, String
from app.db.models.kakao_chatbot_user import get_kakao_chatbot_userBase

Base = get_kakao_chatbot_userBase()

class kakao_chatbot_dream(Base):
    __tablename__ = "kakao_chatbot_dream"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('kakao_chatbot_user.id'), nullable=False)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    dream_name = Column(String(50), nullable=False)

def get_Base():
    return Base
