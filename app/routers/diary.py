from fastapi import APIRouter, Depends
from app.schemas.common import ApiResponse
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.schemas.response.diary import DiaryResponse
from app.schemas.response.user import User
from app.schemas.request.crud import Create, Update
from app.crud.diary import createDiary, readDiary, deleteDiary, updateDiary, likeDiary, unlikeDiary

router = APIRouter(prefix="/diary")
@router.post("/create", response_model=ApiResponse, tags=["Diary"])
async def create_diary(
    create: Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await createDiary(create, current_user.id, db)
    return ApiResponse(
        success=True,
        data={
            "message": "일기가 성공적으로 작성되었습니다."
        }
    )

@router.get("/read", response_model=ApiResponse, tags=["Diary"])
async def read_diary(
    diary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_public, is_owner, create_date, modified_date, image_url, view_count, like_count, dream_name, dream, is_modified = await readDiary(diary_id, current_user.id, db)
    return ApiResponse(
        success=True,
        data=DiaryResponse(
            is_public=is_public,
            create_date=create_date,
            modified_date=modified_date,
            image_url=image_url,
            view_count=view_count,
            like_count=like_count,
            dream_name=dream_name,
            dream=dream,
            is_owner=is_owner,
            is_modified=is_modified,
        )
    )
@router.post("/update", response_model=ApiResponse, tags=["Diary"])
async def update_diary(
    diary_id: int,
    create: Update,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await updateDiary(diary_id, current_user.id, create, db)
    return ApiResponse(
        success=True,
        data={
            "message": "일기가 성공적으로 수정되었습니다."
        }
    )
@router.delete("/delete", response_model=ApiResponse, tags=["Diary"])
async def delete_diary(
    diary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await deleteDiary(diary_id, current_user.id, db)
    return ApiResponse(
        success=True,
        data={
            "message": "일기가 성공적으로 삭제되었습니다."
        }
    )

@router.post("/like", response_model=ApiResponse, tags=["Diary"])
async def like_diary(
    diary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await likeDiary(diary_id, current_user.id, db)
    return ApiResponse(
        success=True,
        data={
            "message": "일기가 성공적으로 좋아요 되었습니다."
        }
    )

@router.post("/unlike", response_model=ApiResponse, tags=["Diary"])
async def unlike_diary(
    diary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await unlikeDiary(diary_id, current_user.id, db)
    return ApiResponse(
        success=True,
        data={
            "message": "일기가 성공적으로 좋아요 취소되었습니다."
        }
    )