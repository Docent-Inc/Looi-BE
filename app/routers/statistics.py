from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.response import ApiResponse
from app.service.statistics import StatisticsService

router = APIRouter(prefix="/statistics")


@router.get("/ratio", response_model=ApiResponse, tags=["Statistics"])
async def get_statistics_ratio(
    statistics_service: Annotated[StatisticsService, Depends()],
) -> ApiResponse:
    ratio = await statistics_service.ratio()
    return ApiResponse(
        data={"ratio": ratio}
    )