from fastapi import APIRouter, Depends
from app.feature.gptapi.generateDream import generate_text
from app.feature.gptapi.generateCheckList import generate_checklist
from app.schemas.response.gpt import BasicResponse, ImageResponse, CheckListResponse
from app.schemas.common import ApiResponse
from app.feature.gptapi.generateImg import additional_generate_image
from app.core.security import get_current_user
from app.schemas.response.user import User
from app.db.database import get_db
from sqlalchemy.orm import Session
router = APIRouter(prefix="/generate")

@router.get("/dream", response_model=ApiResponse, tags=["Generate"])
async def generate_basic(
    text: str, # 사용자가 입력한 텍스트
    db: Session = Depends(get_db), # 데이터베이스 세션
    current_user: User = Depends(get_current_user), # 로그인한 사용자의 정보
) -> BasicResponse:
    dream_name, dream, dream_image_url = await generate_text(text, current_user.id, db)
    return ApiResponse(
        success=True,
        data=BasicResponse(
            dream_name=dream_name,
            dream=dream,
            image_url=dream_image_url
        )
    )

@router.get("/image", response_model=ApiResponse, tags=["Generate"])
async def generate_image(
    textId: int, # 생성된 꿈 텍스트의 id
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImageResponse:
    dream_image_url = await additional_generate_image(textId, current_user.id, db)
    return ApiResponse(
        success=True,
        data=ImageResponse(
            image_url=dream_image_url
        )
    )

@router.get("/checklist", response_model=ApiResponse, tags=["Generate"])
async def generate_image(
    textId: int, # 생성된 꿈 텍스트의 id
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImageResponse:
    dream_resolution, today_checklist = await generate_checklist(textId, current_user.id, db)
    return ApiResponse(
        success=True,
        data=CheckListResponse(
            dream_resolution=dream_resolution,
            today_checklist=today_checklist
        )
    )