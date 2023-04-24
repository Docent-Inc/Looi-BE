from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash
from app.schemas.request.user import UserCreate
from typing import Optional
from app.core.security import get_user_by_email
from app.db.models import User

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        nickName=user.nickName,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_deleted=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email) # 이메일로 사용자 정보 가져오기
    if not user:
        return None
    if not verify_password(password, user.hashed_password): # 비밀번호 확인
        return None
    return user
