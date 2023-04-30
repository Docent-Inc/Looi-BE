from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash
from app.schemas.request.user import UserCreate
from typing import Optional
from app.core.security import get_user_by_email, get_user_by_nickName
from app.db.models import User
from fastapi import HTTPException, status

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

def changeNickName(requset_nickName: str, current_user: User, db: Session) -> Optional[User]:
    existing_user = get_user_by_nickName(db, nickName=requset_nickName)  # 닉네임으로 사용자를 조회합니다.
    if existing_user:  # 사용자가 존재하면
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NickName already registered",  # 에러 메시지를 반환합니다.
        )
    # 닉네임을 변경합니다.
    current_user.nickName = requset_nickName
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

def changePassword(request_password: str, current_user: User, db: Session) -> Optional[User]:
    # 증명되지 않은 사용자는 비밀번호를 변경할 수 없습니다.
    if not verify_password(request_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    # 새로운 비밀번호를 해시합니다.
    current_user.hashed_password = get_password_hash(request_password)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

def deleteUser(current_user: User, db: Session) -> Optional[User]:
    # 사용자의 삭제 상태를 변경합니다.
    current_user.is_deleted = True
    db.add(current_user)
    db.commit()
    db.refresh(current_user)