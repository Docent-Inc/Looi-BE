from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.auth.user import readUserCount
from app.db.database import get_db
from app.feature.diary import readDiary, createDiary, randomDiary, readDiaryCount, listDiaryByUser
from app.feature.generate_kr import generate_text, generate_resolution_mvp
from app.feature.gptapi.generateImg import additional_generate_image
from app.schemas.common import ApiResponse
from app.schemas.request.crud import Create
from app.schemas.response.diary import DiaryResponse, DiaryListResponse
from app.schemas.response.gpt import BasicResponse, ImageResponse, ResolutionResponse

router = APIRouter(prefix="/mvp")
@router.post("/dream", response_model=ApiResponse, tags=["MVP"])
async def generate_basic(
    text: str, # 사용자가 입력한 텍스트
    db: Session = Depends(get_db),
) -> BasicResponse:
    if len(text) < 10 or len(text) > 200:
        raise HTTPException(
            status_code=400,
            detail="10자 이상 200자 이하로 입력해주세요."
        )

    id, dream_name, dream, dream_image_url = await generate_text(text, 1, db)
    return ApiResponse(
        success=True,
        data=BasicResponse(
            id=id,
            dream_name=dream_name,
            dream=dream,
            image_url=dream_image_url
        )
    )

@router.post("/image", response_model=ApiResponse, tags=["MVP"])
async def generate_image(
    textId: int, # 생성된 꿈 텍스트의 id
    db: Session = Depends(get_db),
) -> ImageResponse:
    dream_image_url = await additional_generate_image(textId, 1, db)
    return ApiResponse(
        success=True,
        data=ImageResponse(
            image_url=dream_image_url
        )
    )

@router.post("/resolution", response_model=ApiResponse, tags=["MVP"])
async def resolution(
    text: str, # 생성된 꿈 텍스트의 id
) -> ResolutionResponse:
    if len(text) < 10 or len(text) > 200:
        raise HTTPException(
            status_code=400,
            detail="10자 이상 200자 이하로 입력해주세요."
        )

    dream_resolution = await generate_resolution_mvp(text)
    return ApiResponse(
        success=True,
        data=ResolutionResponse(
            dream_resolution=dream_resolution
        )
    )

@router.post("/save", response_model=ApiResponse, tags=["MVP"])
async def save(
    create: Create,
    db: Session = Depends(get_db),
):
    diary_id = await createDiary(create, 1, db)
    return ApiResponse(
        success=True,
        data={
            "id": diary_id,
            "message": "일기가 성공적으로 작성되었습니다."
        }
    )

@router.get("/read", response_model=ApiResponse, tags=["MVP"])
async def read(
    diary_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    is_public, is_owner, create_date, modified_date, image_url, view_count, like_count, dream_name, dream, resolution, checklist, is_modified, comment_count, is_liked = await readDiary(
        diary_id, 1, db, background_tasks)
    return ApiResponse(
        success=True,
        data=DiaryResponse(
            id=diary_id,
            is_public=is_public,
            create_date=create_date,
            modified_date=modified_date,
            image_url=image_url,
            view_count=view_count,
            like_count=like_count,
            dream_name=dream_name,
            dream=dream,
            resolution=resolution,
            checklist=checklist,
            is_owner=is_owner,
            is_modified=is_modified,
            comment_count=comment_count,
            is_liked=is_liked,
        )
    )

@router.get("/random", response_model=ApiResponse, tags=["MVP"])
async def number(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    diary_id = await randomDiary(db)
    is_public, is_owner, create_date, modified_date, image_url, view_count, like_count, dream_name, dream, resolution, checklist, is_modified, comment_count, is_liked = await readDiary(
        diary_id, 1, db, background_tasks)
    return ApiResponse(
        success=True,
        data=DiaryResponse(
            id=diary_id,
            is_public=is_public,
            create_date=create_date,
            modified_date=modified_date,
            image_url=image_url,
            view_count=view_count,
            like_count=like_count,
            dream_name=dream_name,
            dream=dream,
            resolution=resolution,
            checklist=checklist,
            is_owner=is_owner,
            is_modified=is_modified,
            comment_count=comment_count,
            is_liked=is_liked,
        )
    )

@router.get("/user/count", response_model=ApiResponse, tags=["MVP"])
async def user_count(
    db: Session = Depends(get_db),
):
    user_count = await readUserCount(db)
    return ApiResponse(
        success=True,
        data=user_count
    )

@router.get("/diary/count", response_model=ApiResponse, tags=["MVP"])
async def diary_count(
    db: Session = Depends(get_db),
):
    diary_count = await readDiaryCount(db)
    return ApiResponse(
        success=True,
        data=diary_count
    )

@router.get("/count/user", response_model=ApiResponse, tags=["MVP"])
async def user_count(
    user_id: int,
    db: Session = Depends(get_db),
):
    diary_list = await listDiaryByUser(user_id, 1, user_id, db)
    diary_list_response = []
    for diary in diary_list:
        diary_response = DiaryListResponse(
            id=diary.id,
            dream_name=diary.dream_name,
            create_date=diary.create_date,
            dream=diary.dream,
            resolution=diary.resolution,
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

