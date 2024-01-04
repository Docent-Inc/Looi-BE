from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.db.models import User
from app.schemas.response import ApiResponse
from app.service.share import ShareService

router = APIRouter(prefix="/share")

@router.get("/dream/link/{dream_id}", response_model=ApiResponse, tags=["Share"])
async def get_share_dream_link(
    dream_id: int,
    share_service: Annotated[ShareService, Depends()],
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse:
    link = await share_service.dream_link(user, dream_id)
    return ApiResponse(
        data={"id": link}
    )

@router.get("/diary/link/{diary_id}", response_model=ApiResponse, tags=["Share"])
async def get_share_diary_link(
    diary_id: int,
    share_service: Annotated[ShareService, Depends()],
) -> ApiResponse:
    link = await share_service.diary_link(diary_id)
    return ApiResponse(
        data={"id": link}
    )


@router.get("/{share_id}", response_model=ApiResponse, tags=["Share"])
async def share_morning_diary(
    share_id: str,
    share_service: Annotated[ShareService, Depends()],
) -> ApiResponse:
    diary = await share_service.read(share_id)
    return ApiResponse(
        data={"diary": diary}
    )
