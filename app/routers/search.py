from app.db.models.user import User
from app.feature.search import listHot, listText, listSearchHistory, deleteSearchHistory, deleteSearchHistoryAll
from app.schemas.common import ApiResponse
from fastapi import APIRouter, Depends
from app.db.database import get_db
from app.core.security import get_current_user
from sqlalchemy.orm import Session

from app.schemas.response.diary import DiaryListResponse
router = APIRouter(prefix="/search")

@router.get("/hot/{page}", response_model=ApiResponse, tags=["Search"])
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

@router.get("/text/{text}/{page}", response_model=ApiResponse, tags=["Search"])
async def search_text(
    text: str,
    page: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    text_list = await listText(page, text, db, current_user.id)
    return ApiResponse(
        success=True,
        data=text_list
    )

@router.get("/histories", response_model=ApiResponse, tags=["Search"])
async def search_histories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    search_history_list = await listSearchHistory(current_user.id, db)
    return ApiResponse(
        success=True,
        data=search_history_list
    )

@router.delete("/histories/{id}", response_model=ApiResponse, tags=["Search"])
async def delete_search_histories(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await deleteSearchHistory(id, current_user.id, db)
    return ApiResponse(
        success=True,
        data="검색 기록이 삭제되었습니다."
    )

@router.delete("/histories/all", response_model=ApiResponse, tags=["Search"])
async def delete_search_histories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await deleteSearchHistoryAll(current_user.id, db)
    return ApiResponse(
        success=True,
        data="검색 기록이 전체 삭제되었습니다."
    )