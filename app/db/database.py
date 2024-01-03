from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.db.models import get_Base
import redis
import aioredis

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)
DB_URL = f'mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_ADDRESS}/{settings.DB_NAME}'
engine = create_engine(DB_URL, pool_recycle=3600)

Base = get_Base()
def get_Base():
    return Base

# Base.metadata.drop_all(bind=engine) # 테이블 변경 사항 있을 시 주석 제거
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_SessionLocal():
    return SessionLocal

async def get_redis_client():
    return aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}", encoding="utf-8", decode_responses=True)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def save_db(data, db):
    try:
        db.add(data)
        db.commit()
        db.refresh(data)
        return data
    except:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=5000,
        )