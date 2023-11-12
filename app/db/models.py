from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean, DateTime, func, JSON, Date, FLOAT
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
    is_admin = Column(Boolean, default=False)
    subscription_status = Column(Boolean, default=False)
    image_model = Column(Integer, nullable=True)
    language_id = Column(Integer, nullable=True)
    Oauth_from = Column(String(10), nullable=True)
    birth = Column(Date, nullable=True, default=func.now())
    push_token = Column(String(100), nullable=True)
    push_morning = Column(Boolean, default=True)
    push_night = Column(Boolean, default=True)
    push_report = Column(Boolean, default=True)
    create_date = Column(DateTime, nullable=False)
    deleted_date = Column(DateTime, nullable=True)


class MorningDiary(Base):
    __tablename__ = "MorningDiary"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='morning_diaries')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    diary_name = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    image_url = Column(String(100), nullable=True)
    background_color = Column(String(50), nullable=True)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    is_completed = Column(Boolean, default=False, index=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class NightDiary(Base):
    __tablename__ = "NightDiary"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='night_diaries')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    diary_name = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(100), nullable=True)
    background_color = Column(String(50), nullable=True)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Memo(Base):
    __tablename__ = "Memo"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='memos')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

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
    create_date = Column(DateTime, nullable=False)


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
    event_time = Column(DateTime, nullable=True)
    image_url = Column(String(100), nullable=True)
    create_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

class Report(Base):
    __tablename__ = "Report"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='reports')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(100), nullable=True)
    create_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    is_read = Column(Boolean, default=False, index=True)

class Luck(Base):
    __tablename__ = "Luck"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='lucks')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    create_date = Column(Date, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

class Prompt(Base):
    __tablename__ = "Prompt"

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)

class WelcomeChat(Base):
    __tablename__ = "WelcomeChat"

    id = Column(Integer, primary_key=True)
    text = Column(String(200), nullable=True)
    type = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

class HelperChat(Base):
    __tablename__ = "HelperChat"

    id = Column(Integer, primary_key=True)
    text = Column(String(200), nullable=True)
    type = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

class ApiRequestLog(Base):
    __tablename__ = "ApiRequestLog"

    id = Column(Integer, primary_key=True)
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    is_success = Column(Boolean, nullable=False)
    request_type = Column(String(50), nullable=False)
    request_token = Column(Integer, nullable=False)
    response_token = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    model = Column(String(50), nullable=False)
    create_date = Column(DateTime, nullable=False)

class Dashboard(Base):
    __tablename__ = "Dashboard"

    id = Column(Integer, primary_key=True)
    today_user = Column(Integer, nullable=False)
    today_chat = Column(Integer, nullable=False)
    today_cost = Column(FLOAT, nullable=False)
    today_morning_diary = Column(Integer, nullable=False)
    today_night_diary = Column(Integer, nullable=False)
    today_calender = Column(Integer, nullable=False)
    today_memo = Column(Integer, nullable=False)
    create_date = Column(DateTime, nullable=False)

class TextClassification(Base):
    __tablename__ = "TextClassification"

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    text_type = Column(String(10), nullable=False)
    create_date = Column(DateTime, nullable=False)

class ErrorLog(Base):
    __tablename__ = "ErrorLog"

    id = Column(Integer, primary_key=True)
    error_code = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=False)
    create_date = Column(DateTime, nullable=False)

def get_Base():
    return Base