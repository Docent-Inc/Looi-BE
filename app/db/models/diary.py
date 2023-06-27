from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

from app.db.models.dream import get_DreamBase
Base = get_DreamBase()

class Diary(Base):
    __tablename__ = "Diary"

    id = Column(Integer, primary_key=True)
    user = relationship('User', backref='diaries')
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    checklist = Column(Text, nullable=True)
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

def get_DiaryBase():
    return Base


