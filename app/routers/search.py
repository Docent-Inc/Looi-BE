from app.db.models.user import User
from app.feature.search import listHot, listText
from app.schemas.common import ApiResponse
from fastapi import APIRouter, Depends
from app.db.database import get_db
from app.core.security import get_current_user
from sqlalchemy.orm import Session

from app.schemas.response.diary import DiaryListResponse
router = APIRouter(prefix="/search")

@router.get("/hot", response_model=ApiResponse, tags=["Search"])
async def get_hot(
    page: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    diary_list_response = await listHot(page, db, current_user)

    return ApiResponse(
        success=True,
        data=diary_list_response
    )

@router.get("/text", response_model=ApiResponse, tags=["Search"])
async def search_text(
    text: str,
    page: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    text_list = await listText(page, text, db)
    diary_list_response = []
    for diary in text_list:
        diary_response = DiaryListResponse(
            id=diary.id,
            dream_name=diary.dream_name,
            image_url=diary.image_url,
            view_count=diary.view_count,
            like_count=diary.like_count,
            comment_count=diary.comment_count
        )
        diary_list_response.append(diary_response)

    return ApiResponse(
        success=True,
        data=diary_list_response
    )