from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from app.db.models.dream import get_DreamBase
from app.db.models.user import get_UserBase

DB_URL = 'mysql+pymysql://dmz:1234@swiftsjh.tplinkdns.com:3306/docent'
engine = create_engine(DB_URL, pool_recycle=500)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 각 Base의 메타데이터를 병합
merged_metadata = MetaData()
for base in [get_UserBase(), get_DreamBase()]:
    for table in base.metadata.tables.values():
        table.tometadata(merged_metadata)

# 병합된 메타데이터로 새로운 Base 생성
Base = declarative_base(metadata=merged_metadata)
Base.metadata.create_all(bind=engine)  # 테이블 생성

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()