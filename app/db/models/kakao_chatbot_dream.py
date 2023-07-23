from sqlalchemy import Column, Integer, ForeignKey
from app.db.models.kakao_chatbot_user import get_kakao_chatbot_userBase

Base = get_kakao_chatbot_userBase()

class kakao_chatbot_dream(Base):
    __tablename__ = "kakao_chatbot_dream"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('kakao_chatbot_user.id'), nullable=False)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)

def get_kakao_chatbot_dreamBase():
    return Base
