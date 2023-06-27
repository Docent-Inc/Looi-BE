from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db.models.comment import get_CommentBase
Base = get_CommentBase()

class SearchHistory(Base):
    __tablename__ = 'search_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    search_term = Column(String(200))
    search_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="search_history")

def get_SearchHistoryBase():
    return Base