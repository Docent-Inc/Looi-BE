from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGBLOB
from app.db.database import Base
class Dream(Base):
    __tablename__ = "dreams"

    id = Column(Integer, primary_key=True)
    text = Column(Text)
    dream_name = Column(Text)
    dream_resolution = Column(Text)
    image_url = Column(LONGBLOB)
