from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status

from app.db.models import Chat
from app.feature.aiRequset import send_gpt_request, send_gpt4_request
from app.feature.diary import create_morning_diary, create_night_diary, create_memo
from app.feature.generate import generate_image, generate_schedule, generate_report, generate_luck
from app.core.security import get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session

from app.schemas.request import ChatRequest
from app.schemas.response import ApiResponse, User

router = APIRouter(prefix="/generate")

@router.post("/chat", tags=["Generate"])
async def generate_chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    사용자의 택스트를 4가지 카테고리로 분류합니다.
    '''
    try:
        text = body.content
        text_type = int(await send_gpt4_request(1, text))
        # if text_type == 1:
        #
        # elif text_type == 2:
        #
        # elif text_type == 3:
        #
        # elif text_type == 4:
        #
        # else:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=4013
        #     )
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4013
        )
    return ApiResponse(
        data={"text_type": text_type}
    )

@router.post("/chat/list", tags=["Generate"])
async def generate_chat_list(
    page: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    # db에서 사용자의 채팅 리스트를 가져옵니다.
    chat = db.query(Chat).filter(Chat.User_id == current_user.id).order_by(Chat.create_date.desc()).offset((page-1) * 5).limit(5).all()
    return ApiResponse(
        data=chat
    )

@router.get("/report", tags=["Generate"])
async def report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    # db에서 최근 7일간의 MorningDiary, NightDiary, Calendar를 불러옵니다
    report = await generate_report(current_user, db)
    # 그리고 그것을 바탕으로 사용자의 리포트를 생성합니다.
    return ApiResponse(
        data=report
    )
@router.get("/luck", tags=["Generate"])
async def luck(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:

    luck = await generate_luck(current_user, db)
    return ApiResponse(
        data={"luck": luck}
    )