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
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="유저정보 생성을 실패했습니다.",  # 에러 메시지를 반환합니다.
        )

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email) # 이메일로 사용자 정보 가져오기
    if not user:
        return None
    if not verify_password(password, user.hashed_password): # 비밀번호 확인
        return None
    return user

def changeNickName(requset_nickName: str, current_user: User, db: Session):
    existing_user = get_user_by_nickName(db, nickName=requset_nickName)  # 닉네임으로 사용자를 조회합니다.
    if existing_user:  # 사용자가 존재하면
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NickName already registered",  # 에러 메시지를 반환합니다.
        )
    # 닉네임을 변경합니다.
    try:
        current_user.nickName = requset_nickName
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="닉네임 변경이 실패했습니다.",  # 에러 메시지를 반환합니다.
        )


def changePassword(request_password: str, current_user: User, db: Session):
    # 증명되지 않은 사용자는 비밀번호를 변경할 수 없습니다.
    if not verify_password(request_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    # 새로운 비밀번호를 해시합니다.
    current_user.hashed_password = get_password_hash(request_password)
    try:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 변경을 실패했습니다.",  # 에러 메시지를 반환합니다.
        )

def deleteUser(current_user: User, db: Session):
    # 사용자의 삭제 상태를 변경합니다.
    current_user.is_deleted = True
    try:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="유저정보 지우는것을 실패했습니다.",  # 에러 메시지를 반환합니다.
        )

def user_kakao(kakao_data: dict, db: Session) -> Optional[User]:
    # 카카오에서 전달받은 사용자 정보를 변수에 저장합니다.
    try:
        kakao_id = str(kakao_data["id"])
        kakao_email = kakao_data["kakao_account"]["email"]
        kakao_nickname = kakao_email.split("@")[0]
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="카카오에서 유저정보를 받아오는데 실패했습니다.",
        )
    try:
        gender = kakao_data["kakao_account"]["gender"]
    except:
        gender = "0"
    try:
        age_range = kakao_data["kakao_account"]["age_range"]
    except:
        age_range = "0"

    # 카카오에서 전달받은 사용자 정보로 사용자를 조회합니다.
    user = get_user_by_email(db, email=kakao_email)
    # 사용자가 존재하지 않으면 새로운 사용자를 생성합니다.
    if not user:
        user = User(
            email=kakao_email,
            nickName=kakao_nickname,
            hashed_password=get_password_hash(kakao_id),
            gender=str(gender),
            age_range=str(age_range),
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="유저정보를 저장하는데 실패했습니다.",
            )
    return user
