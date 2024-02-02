from typing import Annotated
from fastapi import APIRouter, Depends, BackgroundTasks
from app.schemas.request import CreateDiaryRequest, UpdateDiaryRequest
from app.schemas.response import ApiResponse
from app.service.diary import DiaryService

router = APIRouter(prefix="/diary")

@router.post("/create", response_model=ApiResponse, tags=["Diary"])
async def post_diary_create(
    diary_data: CreateDiaryRequest,
    background_tasks: BackgroundTasks,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    diary = await diary_service.create(diary_data, background_tasks)
    return ApiResponse(
        data={"diary": diary}
    )

@router.patch("/generate", response_model=ApiResponse, tags=["Diary"])
async def patch_diary_generate(
    diary_id: int,
    background_tasks: BackgroundTasks,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await diary_service.generate(diary_id, background_tasks)
    )

@router.get("/read", response_model=ApiResponse, tags=["Diary"])
async def get_diary_read(
    diary_id: int,
    background_tasks: BackgroundTasks,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    diary = await diary_service.read(diary_id, background_tasks)
    return ApiResponse(
        data={"diary": diary}
    )

@router.patch("/update", response_model=ApiResponse, tags=["Diary"])
async def patch_diary_update(
    diary_id: int,
    diary_data: UpdateDiaryRequest,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    diary = await diary_service.update(diary_id, diary_data)
    return ApiResponse(
        data={"diary": diary}
    )

@router.delete("/delete", response_model=ApiResponse, tags=["Diary"])
async def delete_diary_delete(
    diary_id: int,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    await diary_service.delete(diary_id)
    return ApiResponse()

@router.get("/list", response_model=ApiResponse, tags=["Diary"])
async def get_diary_list(
    page: int,
    background_tasks: BackgroundTasks,
    diary_service: Annotated[DiaryService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await diary_service.list(page, background_tasks)
    )
