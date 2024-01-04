from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.response import ApiResponse
from app.service.share import ShareService

router = APIRouter(prefix="/share")

@router.get("/{share_id}", response_model=ApiResponse, tags=["Share"])
async def share_morning_diary(
    share_id: str,
    share_service: Annotated[ShareService, Depends()],
) -> ApiResponse:
    diary = await share_service.read(share_id)
    return ApiResponse(
        data={"diary": diary}
    )
