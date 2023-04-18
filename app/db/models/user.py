from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True, index=True)
    nickName = Column(String(25), unique=True, index=True, nullable=False)
    email = Column(String(25), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

def get_UserBase():
    return Base