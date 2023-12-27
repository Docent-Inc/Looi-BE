from typing import Annotated
from fastapi import APIRouter, Depends, BackgroundTasks
from app.schemas.request import CreateDreamRequest, UpdateDreamRequest
from app.schemas.response import ApiResponse
from app.service.dream import DreamService

router = APIRouter(prefix="/dream")


@router.post("/create", response_model=ApiResponse, tags=["Dream"])
async def post_dream_create(
    dream_data: CreateDreamRequest,
    dream_service: Annotated[DreamService, Depends()]
) -> ApiResponse:
    diary = await dream_service.create(dream_data)
    return ApiResponse(
        data={"diary": diary}
    )

@router.patch("/generate", response_model=ApiResponse, tags=["Dream"])
async def patch_dream_generate(
    dream_id: int,
    dream_service: Annotated[DreamService, Depends()]
) -> ApiResponse:
    return ApiResponse(
        data=await dream_service.generate(dream_id)
    )

@router.get("/read", response_model=ApiResponse, tags=["Dream"])
async def get_dream_read(
    dream_id: int,
    background_tasks: BackgroundTasks,
    dream_service: Annotated[DreamService, Depends()]
) -> ApiResponse:
    diary = await dream_service.read(dream_id, background_tasks)
    return ApiResponse(
        data={"diary": diary}
    )

@router.patch("/update", response_model=ApiResponse, tags=["Dream"])
async def post_dream_update(
    dream_id: int,
    dream_data: UpdateDreamRequest,
    dream_service: Annotated[DreamService, Depends()]
) -> ApiResponse:
    diary = await dream_service.update(dream_id, dream_data)
    return ApiResponse(
        data={"diary": diary}
    )

@router.delete("/delete", response_model=ApiResponse, tags=["Dream"])
async def delete_dream_delete(
    dream_id: int,
    dream_service: Annotated[DreamService, Depends()]
) -> ApiResponse:
    await dream_service.delete(dream_id)
    return ApiResponse()

@router.get("/list", response_model=ApiResponse, tags=["Dream"])
async def get_dream_list(
    page: int,
    background_tasks: BackgroundTasks,
    dream_service: Annotated[DreamService, Depends()]
) -> ApiResponse:
    return ApiResponse(
        data=await dream_service.list(page, background_tasks)
    )