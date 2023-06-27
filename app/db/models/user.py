from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

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

def get_UserBase():
    return Base