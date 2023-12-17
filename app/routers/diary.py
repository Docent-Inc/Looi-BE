from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.request import CreateDiaryRequest, UpdateDiaryRequest
from app.schemas.response import ApiResponse
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

@router.patch("/update", response_model=ApiResponse, tags=["Diary"])
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
