from sqlalchemy import Column, Integer, ForeignKey
from app.db.models.line_chatbot_user import get_Base

Base = get_Base()

class kakao_chatbot_dream(Base):
    __tablename__ = "line_chatbot_dream"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('line_chatbot_user.id'), nullable=False)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)

def get_Base():
    return Base
