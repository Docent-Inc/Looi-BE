from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from app.db.models.mbti_data_KR import get_Base

Base = get_Base()

class kakao_chatbot_user(Base):
    __tablename__ = "kakao_chatbot_user"

    id = Column(Integer, primary_key=True)
    kakao_user_id = Column(Text, nullable=False)
    mbti = Column(String(4), nullable=True)
    day_count = Column(Integer, nullable=False)
    total_generated_dream = Column(Integer, nullable=False)
    status_score = Column(Integer, nullable=False)
    only_luck_count = Column(Integer, nullable=False)
    luck_count = Column(Integer, nullable=False)
    mode = Column(Integer, nullable=False)

class kakao_chatbot_diary(Base):
    __tablename__ = "kakao_chatbot_diary"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('kakao_chatbot_user.id'), nullable=False)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    dream_name = Column(String(50), nullable=False)
    is_deleted = Column(Boolean, nullable=False)

class kakao_chatbot_memo(Base):
    __tablename__ = "kakao_chatbot_memo"

    id = Column(Integer, primary_key=True)
    user_id = Column(Text, nullable=False)
    text = Column(Text, nullable=False)
    is_deleted = Column(Boolean, nullable=False)

class kakao_chatbot_total_chat(Base):
    __tablename__ = "kakao_chatbot_total_chat"

    id = Column(Integer, primary_key=True)
    count = Column(Integer, nullable=False)

def get_kakao_chatbot_userBase():
    return Base
