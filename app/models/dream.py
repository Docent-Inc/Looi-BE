from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGBLOB
from app.db.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = 'mysql+pymysql://dmz:1234@swiftsjh.tplinkdns.com:3306/BMSM'
engine = create_engine(DB_URL)

Base = declarative_base()

class Dream(Base):
    __tablename__ = "dreams_pretotype"

    id = Column(Integer, primary_key=True)
    cookie = Column(Text)
    text = Column(Text)
    dream_name = Column(Text)
    dream_resolution = Column(Text)
    # image_url = Column(LONGBLOB)

Base.metadata.create_all(bind=engine)
