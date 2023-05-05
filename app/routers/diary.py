from fastapi import APIRouter, Depends
from app.schemas.common import ApiResponse
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.schemas.response.diary import DiaryResponse, DiaryListResponse, DiaryUserListResponse
from app.schemas.response.user import User
from app.schemas.request.crud import Create, Update, commentRequest
from app.feature.diary import createDiary, readDiary, deleteDiary, updateDiary, likeDiary, unlikeDiary, commentDiary, \
    uncommentDiary, listDiary, listDiaryByUser

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

@router.delete("/unlike", response_model=ApiResponse, tags=["Diary"])
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

@router.post("/comment", response_model=ApiResponse, tags=["Diary"])
async def comment_diary(
    diary_id: int,
    comment: commentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await commentDiary(diary_id, current_user.id, comment, db)
    return ApiResponse(
        success=True,
        data={
            "message": "댓글이 성공적으로 등록되었습니다."
        }
    )


@router.delete("/uncomment", response_model=ApiResponse, tags=["Diary"])
async def uncomment_diary(
    diary_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await uncommentDiary(diary_id, comment_id, db)
    return ApiResponse(
        success=True,
        data={
            "message": "댓글이 성공적으로 삭제되었습니다."
        }
    )

@router.get("/list", response_model=ApiResponse, tags=["Diary"])
async def list_diary(
    page: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    diary_list = await listDiary(page, current_user.id, db)
    diary_list_response = []
    for diary in diary_list:
        diary_response = DiaryListResponse(
            id=diary.id,
            dream_name=diary.dream_name,
            image_url=diary.image_url,
            view_count=diary.view_count,
            like_count=diary.like_count,
            comment_count=diary.comment_count,
            userNickname=diary.nickname,
            userId=diary.userId,
            is_liked=diary.is_liked,
        )
        diary_list_response.append(diary_response)

    return ApiResponse(
        success=True,
        data=diary_list_response
    )

@router.get("/list/{user_id}", response_model=ApiResponse, tags=["Diary"])
async def list_diary_by_user(
    user_id: int,
    page: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    diary_list = await listDiaryByUser(user_id, page, current_user.id, db)
    diary_list_response = []
    for diary in diary_list:
        diary_response = DiaryUserListResponse(
            id=diary.id,
            dream_name=diary.dream_name,
            image_url=diary.image_url,
            view_count=diary.view_count,
            like_count=diary.like_count,
            comment_count=diary.comment_count,
            userNickname=diary.nickname,
            userId=diary.userId,
            isMine=diary.isMine,
            is_liked=diary.is_liked,
        )
        diary_list_response.append(diary_response)

    return ApiResponse(
        success=True,
        data=diary_list_response
    )

@router.get("/list/mydiary", response_model=ApiResponse, tags=["Diary"])
async def list_my_diary(
    page: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    diary_list = await listDiaryByUser(current_user.id, page, current_user.id, db)
    diary_list_response = []
    for diary in diary_list:
        diary_response = DiaryListResponse(
            id=diary.id,
            dream_name=diary.dream_name,
            image_url=diary.image_url,
            view_count=diary.view_count,
            like_count=diary.like_count,
            comment_count=diary.comment_count,
            userNickname=diary.nickname,
            userId=diary.userId,
            is_liked=diary.is_liked,
        )
        diary_list_response.append(diary_response)

    return ApiResponse(
        success=True,
        data=diary_list_response
    )