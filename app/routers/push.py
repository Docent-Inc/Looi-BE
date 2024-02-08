from typing import Annotated, Optional

from fastapi import APIRouter, Depends

from app.schemas.response import ApiResponse
from app.service.push import PushService

router = APIRouter(prefix="/push")

@router.get("/test", response_model=ApiResponse, tags=["Push"])
async def get_push_test(
    report_service: Annotated[PushService, Depends()],
) -> ApiResponse:
    await report_service.test()
    return ApiResponse()