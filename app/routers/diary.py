from typing import Annotated

from fastapi import APIRouter, Depends
from app.feature.diary import get_diary_ratio, share_read_night_diary
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.schemas.request import CreateDiaryRequest, UpdateDiaryRequest
from app.schemas.response import User, ApiResponse
from app.service.diary import DiaryService

router = APIRouter(prefix="/diary")

@router.post("/create", response_model=ApiResponse, tags=["Diary"])
async def post_diary_create(
    diary_data: CreateDiaryRequest,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    diary = await diary_service.create(diary_data)
    return ApiResponse(
        data={"diary": diary}
    )

@router.get("/read", response_model=ApiResponse, tags=["Diary"])
async def night_read(
    diary_id: int,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    diary = await diary_service.read(diary_id)
    return ApiResponse(
        data={"diary": diary}
    )

@router.post("/update", response_model=ApiResponse, tags=["Diary"])
async def night_update(
    diary_id: int,
    diary_data: UpdateDiaryRequest,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    diary = await diary_service.update(diary_id, diary_data)
    return ApiResponse(
        data={"diary": diary}
    )

@router.delete("/delete", response_model=ApiResponse, tags=["Diary"])
async def night_delete(
    diary_id: int,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    await diary_service.delete(diary_id)
    return ApiResponse()

@router.get("/list", response_model=ApiResponse, tags=["Diary"])
async def night_list(
    page: int,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    diaries = await diary_service.list(page)
    return ApiResponse(
        data={"diaries": diaries}
    )





@router.get("/ratio", response_model=ApiResponse, tags=["Diary"])
async def get_ratio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    ratio = await get_diary_ratio(current_user, db)
    return ApiResponse(
        data={"ratio": ratio}
    )

@router.get("/morning/share/{diary_id}", response_model=ApiResponse, tags=["Diary"])
async def share_morning_diary(
    diary_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    diary = await share_read_morning_diary(diary_id, db)
    return ApiResponse(
        data={"diary": diary}
    )

@router.get("/night/share/{diary_id}", response_model=ApiResponse, tags=["Diary"])
async def share_night_diary(
    diary_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    diary = await share_read_night_diary(diary_id, db)
    return ApiResponse(
        data={"diary": diary}
    )
