from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.response import ApiResponse
from app.service.today import TodayService

router = APIRouter(prefix="/today")

@router.get("/calendar", tags=["Today"])
async def get_today_calendar(
    today_service: Annotated[TodayService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await today_service.calendar()
    )
@router.get("/history", tags=["Today"])
async def get_today_history(
    today_service: Annotated[TodayService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await today_service.history()
    )

@router.get("/luck", tags=["Today"])
async def get_today_luck(
    today_service: Annotated[TodayService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await today_service.luck()
    )

@router.get("/weather", tags=["Today"])
async def get_today_weather(
    x: float,
    y: float,
    today_service: Annotated[TodayService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await today_service.weather(x, y)
    )
