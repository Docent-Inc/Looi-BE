from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.feature.diary import readDiary, createDiary
from app.feature.gptapi.generate import generate_text, generate_resolution, generate_checklist, generate_resolution_mvp
from app.feature.gptapi.generateImg import additional_generate_image
from app.schemas.common import ApiResponse
from app.schemas.request.crud import Create
from app.schemas.response.diary import DiaryResponse
from app.schemas.response.gpt import BasicResponse, ImageResponse, ResolutionResponse, CheckListResponse

router = APIRouter(prefix="/mvp")
@router.post("/dream", response_model=ApiResponse, tags=["MVP"])
async def generate_basic(
    text: str, # 사용자가 입력한 텍스트
    db: Session = Depends(get_db),
) -> BasicResponse:
    if len(text) < 10 and len(text) > 200:
        return ApiResponse(
            success=False,
            data={
                "message": "10자 이상 200자 이하로 입력해주세요."
            }
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
    dream_resolution = await generate_resolution_mvp(text)
    return ApiResponse(
        success=True,
        data=ResolutionResponse(
            dream_resolution=dream_resolution
        )
    )

@router.post("/checklist", response_model=ApiResponse, tags=["MVP"])
async def checklist(
    resolution: str,
    textId: int, # 생성된 꿈 텍스트의 id
    db: Session = Depends(get_db),
) -> CheckListResponse:
    dream_checklist = await generate_checklist(resolution, textId, db)
    return ApiResponse(
        success=True,
        data=CheckListResponse(
            today_checklist=dream_checklist
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
    db: Session = Depends(get_db),
):
    is_public, is_owner, create_date, modified_date, image_url, view_count, like_count, dream_name, dream, resolution, checklist, is_modified, comment_count, is_liked = await readDiary(
        diary_id, 1, db)
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