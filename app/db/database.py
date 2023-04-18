from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from app.db.models.dream import get_DreamBase
from app.db.models.user import get_UserBase

PUBLIC_IP_ADDRESS = '34.64.33.205' # gcp sdl database
DB_USER = 'docent'
DB_PASSWORD = 'cocone0331'
DB_NAME = 'test'

# TCP 연결을 사용하여 인스턴스에 연결
DB_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{PUBLIC_IP_ADDRESS}/{DB_NAME}'
engine = create_engine(DB_URL, pool_recycle=500)

# 각 Base의 메타데이터를 병합
merged_metadata = MetaData()
for base in [get_UserBase(), get_DreamBase()]:
    for table in base.metadata.tables.values():
        table.tometadata(merged_metadata)

# 병합된 메타데이터로 새로운 Base 생성
Base = declarative_base(metadata=merged_metadata)
Base.metadata.create_all(bind=engine)  # 테이블 생성

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
