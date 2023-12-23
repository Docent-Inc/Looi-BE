from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from app.schemas.request import CreateCalendarRequest, ListCalendarRequest, UpdateCalendarRequest
from app.schemas.response import ApiResponse
from app.service.calendar import CalendarService

router = APIRouter(prefix="/calendar")

@router.post("/create", response_model=ApiResponse, tags=["Calendar"])
async def post_calendar_create(
    calendar_data: CreateCalendarRequest,
    calendar_service: Annotated[CalendarService, Depends()],
) -> ApiResponse:
    calendar = await calendar_service.create(calendar_data)
    return ApiResponse(
        data={"calendar": calendar}
    )

@router.get("/read", response_model=ApiResponse, tags=["Calendar"])
async def get_calendar_read(
    calendar_id: int,
    calendar_service: Annotated[CalendarService, Depends()],
) -> ApiResponse:
    calendar = await calendar_service.read(calendar_id)
    return ApiResponse(
        data={"calendar": calendar}
    )

@router.patch("/update", response_model=ApiResponse, tags=["Calendar"])
async def post_calendar_update(
    calendar_id: int,
    calendar_data: UpdateCalendarRequest,
    calendar_service: Annotated[CalendarService, Depends()],
) -> ApiResponse:
    calendar = await calendar_service.update(calendar_id, calendar_data)
    return ApiResponse(
        data={"calendar": calendar}
    )

@router.delete("/delete", response_model=ApiResponse, tags=["Calendar"])
async def delete_calender_delete(
    calendar_id: int,
    calendar_service: Annotated[CalendarService, Depends()],
) -> ApiResponse:
    await calendar_service.delete(calendar_id)
    return ApiResponse()

@router.get("/list", response_model=ApiResponse, tags=["Calendar"])
async def get_calendar_post(
    calendar_service: Annotated[CalendarService, Depends()],
    year: int,
    month: int,
    day: Optional[int] = 0,
) -> ApiResponse:
    calendars = await calendar_service.list(year, month, day)
    return ApiResponse(
        data={"calendars": calendars}
    )