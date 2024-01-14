import json
from datetime import datetime, timedelta
from typing import Any, Union

import aioredis
import pytz
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi.security.api_key import APIKeyHeader
from app.db.database import get_db, save_db, get_redis_client
from app.db.models import User
from typing import Optional
from app.core.config import settings
access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
API_KEY_NAME = "Authorization"
api_key_header_auth = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def user_to_json(user):
    return json.dumps(
        {
            "id": user.id,
            "nickname": user.nickname,
            "email": user.email,
            "gender": user.gender,
            "age_range": user.age_range,
            "mbti": user.mbti,
            "is_deleted": user.is_deleted,
            "is_admin": user.is_admin,
            "is_sign_up": user.is_sign_up,
            "subscription_status": user.subscription_status,
            "Oauth_from": user.Oauth_from,
            "birth": f"{user.birth}",
            "push_token": user.push_token,
            "push_morning": user.push_morning,
            "push_night": user.push_night,
            "push_report": user.push_report,
            "device": user.device,
        }, ensure_ascii=False
    )

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta: # 만료시간이 설정되어 있으면
        expire = datetime.utcnow() + expires_delta # 현재시간 + 만료시간
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire}) # 토큰에 만료시간을 추가
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # 토큰을 생성
    return encoded_jwt, expire

async def decode_access_token(token: str) -> Union[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # 토큰을 복호화
        return payload
    except JWTError:
        return None

async def check_token(token_refresh: str, db: Session) -> User:
    payload = await decode_access_token(token_refresh)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4004,
        )
    email: str = payload.get("sub")
    user = db.query(User).filter(User.email == email, User.is_deleted == False).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4005,
        )
    if user.is_sign_up == True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4998,
        )
    return user

def update_user_last_active_date(db: Session, email: str):
    user = db.query(User).filter(User.email == email, User.is_deleted == False).first()
    if user:
        user.last_active_date = datetime.now(pytz.timezone("Asia/Seoul"))
        save_db(user, db)

async def get_current_user(
    background_tasks: BackgroundTasks,
    redis: aioredis.Redis = Depends(get_redis_client),
    api_key: str = Depends(api_key_header_auth), # api_key_header_auth를 통해 api_key를 받아온다.
    db: Session = Depends(get_db),
) -> User:

    # api_key가 없으면
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=4220,
        headers={"WWW-Authenticate": "Bearer"},
    )

    if settings.SERVER_TYPE == "local":
        api_key = settings.TEST_TOKEN
    try:
        # 토큰을 복호화
        token = api_key.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        # 토큰에 email이 없으면
        if email is None:
            raise credentials_exception
    except:
        raise credentials_exception

    user_info = await redis.get(f"user:{email}")
    if user_info:
        background_tasks.add_task(update_user_last_active_date, db=db, email=email)
        return User(**json.loads(user_info))

    # db에서 email로 유저를 찾는다.
    user = db.query(User).filter(User.email == email, User.is_deleted == False).first()
    db.close()
    if user:
        background_tasks.add_task(update_user_last_active_date, db=db, email=email)

    # 유저가 없거나 삭제된 유저면
    if user is None or user.is_deleted == True:
        raise credentials_exception


    # 유저가 로그인이 완료되지 않은 유저라면
    if user.mbti == "0":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4998,
        )

    # 유저 정보를 redis에 저장
    await redis.set(f"user:{email}", await user_to_json(user), ex=3600)  # redis에 유저 정보를 저장

    # 유저 정보 반환
    return user

async def get_update_user(
    api_key: str = Depends(api_key_header_auth), # api_key_header_auth를 통해 api_key를 받아온다.
    db: Session = Depends(get_db),
) -> User:

    # api_key가 없으면
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=4220,
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 테스트 토큰이 아니면
    if settings.SERVER_TYPE == "local":
        api_key = settings.TEST_TOKEN
    try:
        # 토큰을 복호화
        token = api_key.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        # 토큰에 email이 없으면
        if email is None:
            raise credentials_exception
    except:
        raise credentials_exception


    # db에서 email로 유저를 찾는다.
    user = db.query(User).filter(User.email == email, User.is_deleted == False).first()

    # 유저가 없거나 삭제된 유저면
    if user is None or user.is_deleted == True:
        raise credentials_exception

    # 유저의 마지막 로그인 시간을 현재시간으로 변경
    user.last_active_date = await time_now()
    user = save_db(user, db)

    # 유저 정보 반환
    return user

async def get_current_user_is_admin(
    User: User = Depends(get_current_user),
) -> User:
    if User.is_admin == False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4402,
        )
    return User

async def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy() # data를 복사
    if expires_delta: # 만료시간이 설정되어 있으면
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "refresh"}) # 토큰에 만료시간과 type을 추가
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # 토큰을 생성
    return encoded_jwt, expire

async def create_token(email):
    access_token, expires_in = await create_access_token(  # 액세스 토큰을 생성합니다.
        data={"sub": email}, expires_delta=access_token_expires
    )
    refresh_token, refresh_expires_in = await create_refresh_token(  # 리프레시 토큰을 생성합니다.
        data={"sub": email}, expires_delta=refresh_token_expires
    )
    expires_in_seconds = int((expires_in - datetime.utcnow()).total_seconds()) + 1
    refresh_expires_in_seconds = int((refresh_expires_in - datetime.utcnow()).total_seconds()) + 1

    return expires_in_seconds, refresh_expires_in_seconds, access_token, refresh_token

async def check_length(text: str, max_length: int, error_code: int) -> None:
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_code,
        )
    return text

async def time_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

def datetime_serializer(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError("Object of type '%s' is not JSON serializable" % type(o).__name__)

def diary_serializer(diary):
    # 모델의 __dict__ 속성을 사용하여 딕셔너리로 변환
    diary_dict = diary.__dict__.copy()
    diary_dict.pop('_sa_instance_state', None)

    # datetime 객체 처리
    for key, value in diary_dict.items():
        if isinstance(value, datetime):
            diary_dict[key] = value.isoformat()

    return diary_dict