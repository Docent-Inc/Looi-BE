from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class kakao_chatbot_dream(Base):
    __tablename__ = "kakao_chatbot_dream"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('kakao_chatbot_user.id'), nullable=False)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    dream_name = Column(String(50), nullable=False)

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

class line_chatbot_dream(Base):
    __tablename__ = "line_chatbot_dream"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('line_chatbot_user.id'), nullable=False)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)

class line_chatbot_user(Base):
    __tablename__ = "line_chatbot_user"

    id = Column(Integer, primary_key=True)
    line_user_id = Column(Text, nullable=False)
    mbti = Column(String(4), nullable=True)
    day_count = Column(Integer, nullable=False)
    only_luck_count = Column(Integer, nullable=False)
    luck_count = Column(Integer, nullable=False)
    total_generated_dream = Column(Integer, nullable=False)

class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True, index=True)
    nickName = Column(String(25), unique=True, index=True, nullable=False)
    email = Column(String(25), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    gender = Column(String(10), nullable=True)
    age_range = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    subscription_status = Column(Boolean, default=False)
    language_id = Column(Integer, nullable=True)
    search_history = relationship("SearchHistory", back_populates="user")

class SearchHistory(Base):
    __tablename__ = 'search_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    search_term = Column(String(200))
    search_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="search_history")

class Diary(Base):
    __tablename__ = "Diary"

    id = Column(Integer, primary_key=True)
    user = relationship('User', backref='diaries')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    image_url = Column(String(100), nullable=True)
    create_date = Column(String(14), nullable=False)
    modify_date = Column(String(14), nullable=False)
    is_deleted = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    report_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    is_modified = Column(Boolean, default=False)

class Diary_EN(Base):
    __tablename__ = "Diary_EN"

    id = Column(Integer, primary_key=True)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    dream_name = Column(Text, nullable=False)
    dream = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    today_luck = Column(Text, nullable=True)

class Diary_JP(Base):
    __tablename__ = "Diary_JP"

    id = Column(Integer, primary_key=True)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    dream_name = Column(Text, nullable=False)
    dream = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    today_luck = Column(Text, nullable=True)

class Diary_KR(Base):
    __tablename__ = "Diary_KR"

    id = Column(Integer, primary_key=True)
    diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    dream_name = Column(Text, nullable=False)
    dream = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    today_luck = Column(Text, nullable=True)

class Mbti_data_KR(Base):
    __tablename__ = "MBTI_data_KR"

    id = Column(Integer, primary_key=True)
    user_text = Column(Text, nullable=False)
    mbti_resolution = Column(Text, nullable=False)

class Mbti_data_JP(Base):
    __tablename__ = "MBTI_data_JP"

    id = Column(Integer, primary_key=True)
    user_text = Column(Text, nullable=False)
    mbti_resolution = Column(Text, nullable=False)

class Mbti_data_EN(Base):
    __tablename__ = "MBTI_data_EN"

    id = Column(Integer, primary_key=True)
    user_text = Column(Text, nullable=False)
    mbti_resolution = Column(Text, nullable=False)

def get_Base():
    return Base

