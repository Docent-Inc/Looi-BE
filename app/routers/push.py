from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.response import ApiResponse
from app.service.push import PushService

router = APIRouter(prefix="/push")

@router.get("/test", response_model=ApiResponse, tags=["Push"])
async def get_push_test(
    title: str,
    body: str,
    landing_url: str,
    image_url: str,
    token: str,
    report_service: Annotated[PushService, Depends()],
) -> ApiResponse:
    await report_service.test(title, body, landing_url, image_url, token)
    return ApiResponse()