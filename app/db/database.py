from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.db.models import get_Base
import redis

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)
DB_URL = f'mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_ADDRESS}/{settings.DB_NAME}'
engine = create_engine(DB_URL, pool_recycle=150)

Base = get_Base()
def get_Base():
    return Base

# Base.metadata.drop_all(bind=engine) # 테이블 변경 사항 있을 시 주석 제거
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_SessionLocal():
    return SessionLocal
def get_redis_client():
    return redis_client

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
