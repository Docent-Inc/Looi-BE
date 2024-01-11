from typing import Annotated, Optional

from fastapi import APIRouter, Depends

from app.schemas.response import ApiResponse
from app.service.push import PushService

router = APIRouter(prefix="/push")

@router.get("/test", response_model=ApiResponse, tags=["Push"])
async def get_push_test(
    title: str,
    body: str,
    token: str,
    device: str,
    report_service: Annotated[PushService, Depends()],
    image_url: Optional[str] = "",
    landing_url: Optional[str] = "",
) -> ApiResponse:
    await report_service.test(title, body, landing_url, image_url, token, device)
    return ApiResponse()