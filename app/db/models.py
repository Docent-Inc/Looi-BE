from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean, DateTime, func, JSON, Date, FLOAT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(50), index=True, nullable=False)
    email = Column(String(50), index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
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
    push_token = Column(String(300), nullable=True)
    push_morning = Column(Boolean, default=True)
    push_night = Column(Boolean, default=True)
    push_report = Column(Boolean, default=True)
    create_date = Column(DateTime, nullable=False)
    deleted_date = Column(DateTime, nullable=True)
    is_sign_up = Column(Boolean, default=True)
    last_active_date = Column(DateTime, nullable=True)


class MorningDiary(Base):
    __tablename__ = "MorningDiary"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='morning_diaries')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    diary_name = Column(String(255), nullable=False)
    content = Column(String(1000), nullable=False)
    resolution = Column(String(1000), nullable=True)
    image_url = Column(String(200), nullable=True)
    background_color = Column(String(50), nullable=True)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    is_generated = Column(Boolean, default=False, index=True)
    main_keyword = Column(String(200), nullable=True)
    view_count = Column(Integer, default=1, nullable=True)
    share_count = Column(Integer, default=0, nullable=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class NightDiary(Base):
    __tablename__ = "NightDiary"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='night_diaries')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    diary_name = Column(String(255), nullable=False)
    content = Column(String(1000), nullable=False)
    image_url = Column(String(200), nullable=True)
    background_color = Column(String(50), nullable=True)
    resolution = Column(String(1000), nullable=True)
    main_keyword = Column(String(200), nullable=True)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_generated = Column(Boolean, default=False, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    is_generated = Column(Boolean, default=False, index=True)
    view_count = Column(Integer, default=1, nullable=True)
    share_count = Column(Integer, default=0, nullable=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Memo(Base):
    __tablename__ = "Memo"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='memos')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String(1000), nullable=False)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)
    is_generated = Column(Boolean, default=False, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    tags = Column(String(100), nullable=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Calendar(Base):
    __tablename__ = "Calendar"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='calenders')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    title = Column(String(255), nullable=False)
    is_generated = Column(Boolean, default=False, index=True)
    content = Column(String(255), nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    create_date = Column(DateTime, nullable=False)

class Report(Base):
    __tablename__ = "Report"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='reports')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    content = Column(String(5000), nullable=False)
    image_url = Column(String(100), nullable=True)
    create_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    is_read = Column(Boolean, default=False, index=True)

class Luck(Base):
    __tablename__ = "Luck"

    id = Column(Integer, primary_key=True)
    User = relationship('User', backref='lucks')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    text = Column(String(1000), nullable=False)
    content = Column(String(500), nullable=False)
    create_date = Column(Date, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)

class Prompt(Base):
    __tablename__ = "Prompt"

    id = Column(Integer, primary_key=True)
    text = Column(String(1000), nullable=False)
    prompt = Column(String(1000), nullable=False)

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
    today_record = Column(Integer, nullable=False)
    today_cost = Column(FLOAT, nullable=False)
    today_dream = Column(Integer, nullable=False)
    today_diary = Column(Integer, nullable=False)
    today_calendar = Column(Integer, nullable=False)
    today_memo = Column(Integer, nullable=False)
    today_mean_request = Column(FLOAT, nullable=False)
    dau = Column(Integer, nullable=False)
    wau = Column(Integer, nullable=False)
    mau = Column(Integer, nullable=False)
    dau_to_mau = Column(FLOAT, nullable=False)
    dau_to_wau = Column(FLOAT, nullable=False)
    create_date = Column(DateTime, nullable=False)
    error_count = Column(Integer, nullable=False)


class TextClassification(Base):
    __tablename__ = "TextClassification"

    id = Column(Integer, primary_key=True)
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    text = Column(String(1000), nullable=False)
    text_type = Column(String(10), nullable=False)
    create_date = Column(DateTime, nullable=False)

class ErrorLog(Base):
    __tablename__ = "ErrorLog"

    id = Column(Integer, primary_key=True)
    error_code = Column(Integer, nullable=False)
    error_message = Column(String(255), nullable=False)
    create_date = Column(DateTime, nullable=False)

class PushQuestion(Base):
    __tablename__ = "PushQuestion"

    id = Column(Integer, primary_key=True)
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False, index=True)
    calendar_content = Column(String(255), nullable=False)
    question = Column(String(255), nullable=False)
    create_date = Column(DateTime, nullable=False)

def get_Base():
    return Base