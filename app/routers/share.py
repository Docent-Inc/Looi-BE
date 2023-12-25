from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.response import ApiResponse
from app.service.share import ShareService

router = APIRouter(prefix="/share")

@router.get("/dream/{dream_id}", response_model=ApiResponse, tags=["Share"])
async def share_morning_diary(
    dream_id: int,
    share_service: Annotated[ShareService, Depends()],
) -> ApiResponse:
    diary = await share_service.dream_read(dream_id)
    return ApiResponse(
        data={"diary": diary}
    )

@router.get("/diary/{diary_id}", response_model=ApiResponse, tags=["Share"])
async def share_night_diary(
    diary_id: int,
    share_service: Annotated[ShareService, Depends()],
) -> ApiResponse:
    diary = await share_service.diary_read(diary_id)
    return ApiResponse(
        data={"diary": diary}
    )
