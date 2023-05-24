from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.models.search import get_SearchHistoryBase

PUBLIC_IP_ADDRESS = '34.64.33.205' # gcp sql database
DB_USER = 'docent'
DB_PASSWORD = 'cocone0331'
DB_NAME = 'test'

# TCP 연결을 사용하여 인스턴스에 연결
DB_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{PUBLIC_IP_ADDRESS}/{DB_NAME}'
engine = create_engine(DB_URL, pool_recycle=150)

Base = get_SearchHistoryBase()
def get_Base():
    return Base

# Base.metadata.drop_all(bind=engine) # 테이블 변경 사항 있을 시 주석 제거
Base.metadata.create_all(bind=engine)  # 테이블 생성

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session: # db 세션 생성
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
