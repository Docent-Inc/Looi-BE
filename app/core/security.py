from datetime import datetime, timedelta
from typing import Any, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi.security.api_key import APIKeyHeader
from app.db.database import get_db
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

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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

async def get_current_user(
    api_key: str = Depends(api_key_header_auth), # api_key_header_auth를 통해 api_key를 받아온다.
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=4220,
        headers={"WWW-Authenticate": "Bearer"},
    )
    if settings.TEST_TOKEN != "test":
        api_key = settings.TEST_TOKEN
    try:
        token = api_key.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None or user.is_deleted == True:
        raise credentials_exception
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
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email, User.is_deleted == False).first()

def get_user_by_nickname(db: Session, nickname: str) -> Optional[User]:
    return db.query(User).filter(User.nickname == nickname, User.is_deleted == False).first()

async def create_token(email):
    access_token, expires_in = await create_access_token(  # 액세스 토큰을 생성합니다.
        data={"sub": email}, expires_delta=access_token_expires
    )
    refresh_token,refresh_expires_in = await create_refresh_token(  # 리프레시 토큰을 생성합니다.
        data={"sub": email}, expires_delta=refresh_token_expires
    )
    expires_in_seconds = int((expires_in - datetime.utcnow()).total_seconds()) + 1
    refresh_expires_in_seconds = int((refresh_expires_in - datetime.utcnow()).total_seconds()) + 1

    return expires_in_seconds, refresh_expires_in_seconds, access_token, refresh_token

async def text_length(text: str, max_length: int):
    min_length = 5
    if len(text) < min_length or len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4221,
        )
    return text
