from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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

class kakao_chatbot_MorningDiary(Base):
    __tablename__ = "kakao_chatbot_MorningDiary"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('kakao_chatbot_user.id'), nullable=False, index=True)
    diary_id = Column(Integer, ForeignKey('MorningDiary.id'), nullable=False)
    diary_name = Column(Text, nullable=False)

class kakao_chatbot_NightDiary(Base):
    __tablename__ = "kakao_chatbot_NightDiary"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('kakao_chatbot_user.id'), nullable=False, index=True)
    diary_id = Column(Integer, ForeignKey('NightDiary.id'), nullable=False)
    diary_name = Column(String(50), nullable=False)

class kakao_chatbot_Memo(Base):
    __tablename__ = "kakao_chatbot_Memo"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('kakao_chatbot_user.id'), nullable=False, index=True)
    memo_id = Column(Integer, ForeignKey('Memo.id'), nullable=False)

class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(25), index=True, nullable=False)
    email = Column(String(25), index=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    gender = Column(String(5), nullable=True)
    age_range = Column(String(5), nullable=True)
    mbti = Column(String(4), nullable=True)
    is_deleted = Column(Boolean, default=False)
    subscription_status = Column(Boolean, default=False)
    language_id = Column(Integer, nullable=True)

class MorningDiary(Base):
    __tablename__ = "MorningDiary"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='morning_diaries')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    diary_name = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    image_url = Column(String(100), nullable=True)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    is_modified = Column(Boolean, default=False)

class NightDiary(Base):
    __tablename__ = "NightDiary"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='night_diaries')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    diary_name = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

class Memo(Base):
    __tablename__ = "Memo"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='memos')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    memo = Column(Text, nullable=False)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

class Calender(Base):
    __tablename__ = "Calender"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='calenders')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

def get_Base():
    return Base