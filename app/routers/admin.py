from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, func, case
from sqlalchemy.orm import Session
from starlette import status

from app.core.security import get_current_user, get_current_user_is_admin
from app.db.database import get_db, save_db
from app.db.models import User, WelcomeChat, HelperChat, Dashboard, TextClassification
from app.feature.slackBot import slack_bot
from app.schemas.request import WelcomeRequest, HelperRequest
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/admin")

@router.get("/user/info", response_model=ApiResponse, tags=["Admin"])
async def get_user_info(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    # 유저 정보
    user = db.query(User).filter(User.id == user_id).first()

    # 비밀 번호 제거
    if user:
        user.hashed_password = None
        return ApiResponse(data=user)

    # 유저 정보 없음
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4401,
        )

@router.post("/welcome", response_model=ApiResponse, tags=["Admin"])
async def post_welcome(
    request: WelcomeRequest,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    # 환영 인사 저장
    new_data = WelcomeChat(
        text=request.text,
        type=request.type,
    )
    save_db(new_data, db)

    # 응답
    return ApiResponse()

@router.get("/welcome/list", response_model=ApiResponse, tags=["Admin"])
async def get_welcome_list(
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    # 환영 인사 리스트
    data = db.query(WelcomeChat).filter(WelcomeChat.is_deleted==False).all()

    # 응답
    return ApiResponse(data=data)
@router.delete("/welcome", response_model=ApiResponse, tags=["Admin"])
async def delete_welcome(
    welcome_id: int,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):

    # 환영 인사 삭제
    data = db.query(WelcomeChat).filter(WelcomeChat.id == welcome_id).first()
    data.is_deleted = True
    save_db(data, db)

    # 응답
    return ApiResponse()

@router.post("/helper", response_model=ApiResponse, tags=["Admin"])
async def post_helper(
    request: HelperRequest,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):

    # 도움말 저장
    new_data = HelperChat(
        text=request.text,
        type=request.type,
    )
    save_db(new_data, db)

    # 응답
    return ApiResponse()
@router.get("/helper/list", response_model=ApiResponse, tags=["Admin"])
async def get_helper_list(
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    # 도움말 리스트
    data = db.query(HelperChat).filter(HelperChat.is_deleted==False).all()

    # 응답
    return ApiResponse(data=data)

@router.delete("/helper", response_model=ApiResponse, tags=["Admin"])
async def delete_helper(
    helper_id: int,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    # 도움말 삭제
    data = db.query(HelperChat).filter(HelperChat.id == helper_id).first()
    data.is_deleted = True
    save_db(data, db)

    # 응답
    return ApiResponse()

@router.get("/user/list", response_model=ApiResponse, tags=["Admin"])
async def get_user_list(
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    # 유저 리스트
    users = db.query(User).all()
    user_list = []

    # 비밀 번호 제거
    for user in users:
        user_dict = {c.key: getattr(user, c.key) for c in inspect(user).mapper.column_attrs}
        user_dict.pop("hashed_password", None)  # hashed_password 키를 제거합니다.
        user_list.append(user_dict)

    # 응답
    response_data = {"data": user_list}
    return ApiResponse(**response_data)

@router.get("/dashboard", response_model=ApiResponse, tags=["Admin"])
async def get_dashboard(
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    # 대시보드 정보
    dashboard = db.query(Dashboard).all()

    # 응답
    return ApiResponse(data=dashboard)

@router.get("/text", response_model=ApiResponse, tags=["Admin"])
async def get_text(
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    # 텍스트 기록 정보
    text = db.query(TextClassification).all()

    # 응답
    return ApiResponse(data=text)

@router.post("/now", response_model=ApiResponse, tags=["Admin"])
async def get_now(
    db: Session = Depends(get_db),
):
    # 현재 서비스 정보를 응답.(슬렉 봇으로 응답)
    await slack_bot()
    return ApiResponse()

@router.get("/user_chat", response_model=ApiResponse, tags=["Admin"])
async def get_user_chat(
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    # 유저별 채팅 기록 및 카테고리별 기록 횟수
    chat_data = (
        db.query(
            User.nickname,
            func.date(TextClassification.create_date).label('chat_date'),
            func.count(TextClassification.id).label('total_chats'),
            func.sum(case((TextClassification.text_type == '꿈', 1), else_=0)).label('dream_count'),
            func.sum(case((TextClassification.text_type == '일기', 1), else_=0)).label('diary_count'),
            func.sum(case((TextClassification.text_type == '일정', 1), else_=0)).label('schedule_count'),
            func.sum(case((TextClassification.text_type == '메모', 1), else_=0)).label('memo_count')
        )
        .join(TextClassification, User.id == TextClassification.User_id)
        .group_by(User.nickname, 'chat_date')
        .order_by(User.nickname, 'chat_date')
        .all()
    )

    # 결과를 딕셔너리 형태로 변환하여 반환
    chat_dict = {}
    for record in chat_data:
        if record.nickname not in chat_dict:
            chat_dict[record.nickname] = {}
        chat_dict[record.nickname][str(record.chat_date)] = {
            'total_chats': record.total_chats,
            'dream_count': record.dream_count,
            'diary_count': record.diary_count,
            'schedule_count': record.schedule_count,
            'memo_count': record.memo_count
        }

    # 응답
    return ApiResponse(data=chat_dict)