from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean, DateTime, func, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(25), index=True, nullable=False)
    email = Column(String(25), index=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    gender = Column(String(10), nullable=True)
    age_range = Column(String(10), nullable=True)
    mbti = Column(String(4), nullable=True)
    is_deleted = Column(Boolean, default=False)
    subscription_status = Column(Boolean, default=False)
    image_model = Column(Integer, nullable=True)
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
    background_color = Column(String(20), nullable=True)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

class NightDiary(Base):
    __tablename__ = "NightDiary"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='night_diaries')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    diary_name = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(100), nullable=True)
    background_color = Column(String(20), nullable=True)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

class Memo(Base):
    __tablename__ = "Memo"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='memos')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

class Calender(Base):
    __tablename__ = "Calender"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='calenders')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)


class Chat(Base):
    __tablename__ = "Chat"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='chats')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    MorningDiary = relationship('MorningDiary', backref='chats')
    MorningDiary_id = Column(Integer, ForeignKey('MorningDiary.id'), nullable=True, index=True)
    NightDiary = relationship('NightDiary', backref='chats')
    NightDiary_id = Column(Integer, ForeignKey('NightDiary.id'), nullable=True, index=True)
    Memo = relationship('Memo', backref='chats')
    Memo_id = Column(Integer, ForeignKey('Memo.id'), nullable=True, index=True)
    Calender = relationship('Calender', backref='chats')
    Calender_id = Column(Integer, ForeignKey('Calender.id'), nullable=True, index=True)
    is_chatbot = Column(Boolean, nullable=False)
    content_type = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(100), nullable=True)
    create_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

class Report(Base):
    __tablename__ = "Report"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='reports')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    create_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)


def get_Base():
    return Base