from sqlalchemy import Column, Integer, ForeignKey, String, Boolean
from app.db.models.hot import get_HotBase
Base = get_HotBase()

class Comment(Base):
    __tablename__ = "Comment"

    id = Column(Integer, primary_key=True)
    Diary_id = Column(Integer, ForeignKey('Diary.id'), nullable=False)
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    comment = Column(String(100), nullable=False)
    create_date = Column(String(14), nullable=False)
    is_deleted = Column(Boolean, default=False)

def get_CommentBase():
    return Base

