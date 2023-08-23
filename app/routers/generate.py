from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status

from app.feature.aiRequset import send_gpt_request
from app.feature.diary import create_morning_diary, create_night_diary, create_memo
from app.feature.generate import generate_resolution_clova, generate_image, generate_schedule
from app.core.security import get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session

from app.schemas.request import ChatRequest
from app.schemas.response import ApiResponse, User

router = APIRouter(prefix="/generate")

@router.post("/generate/chat", tags=["Generate"])
async def generate_chat(
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    사용자의 택스트를 4가지 카테고리로 분류합니다.
    '''
    try:
        text = body.content
        text_type = int(await send_gpt_request(1, text))
        if text_type == 1:
            background_tasks.add_task(create_morning_diary, text, current_user, db)
            response = "꿈을 분석중이에요. 잠시만 기다려주세요!"
        elif text_type == 2:
            # background_tasks.add_task(create_night_diary, text, current_user, db)
            response = "일기를 그리고 있어요. 잠시만 기다려주세요!"
        elif text_type == 3:
            # await create_memo(body.content, current_user, db)
            response = "메모를 저장하고 있어요. 잠시만 기다려주세요!"
        elif text_type == 4:
            background_tasks.add_task(generate_schedule, text, current_user, db)
            response = "일정을 저장중이에요. 잠시만 기다려주세요!"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4013
            )
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=4013
        )
    return ApiResponse(
        data={"chat": response}
    )