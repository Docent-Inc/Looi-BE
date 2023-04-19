from sqlalchemy import Column, Integer, String, Text
from app.db.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = 'mysql+pymysql://dmz:1234@swiftsjh.tplinkdns.com:3306/BMSM'
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
class Dream(Base):
    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True)
    phone = Column(Text)
    dreamName = Column(Text)


Base.metadata.create_all(bind=engine)
