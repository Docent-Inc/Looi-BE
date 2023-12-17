from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.request import ListCalenderRequest, UpdateCalenderRequest, CreateCalenderRequest
from app.schemas.response import ApiResponse
from app.service.calender import CalenderService

router = APIRouter(prefix="/calender")

@router.post("/create", response_model=ApiResponse, tags=["Calender"])
async def post_calender_create(
    calender_data: CreateCalenderRequest,
    calender_service: Annotated[CalenderService, Depends()],
) -> ApiResponse:
    calender = await calender_service.create(calender_data)
    return ApiResponse(
        data={"calender": calender}
    )

@router.get("/read", response_model=ApiResponse, tags=["Calender"])
async def get_calender_read(
    calender_id: int,
    calender_service: Annotated[CalenderService, Depends()],
) -> ApiResponse:
    calender = await calender_service.read(calender_id)
    return ApiResponse(
        data={"calender": calender}
    )

@router.patch("/update", response_model=ApiResponse, tags=["Calender"])
async def post_calender_update(
    calender_id: int,
    calender_data: UpdateCalenderRequest,
    calender_service: Annotated[CalenderService, Depends()],
) -> ApiResponse:
    calender = await calender_service.update(calender_id, calender_data)
    return ApiResponse(
        data={"calender": calender}
    )

@router.delete("/delete", response_model=ApiResponse, tags=["Calender"])
async def delete_calender_delete(
    calender_id: int,
    calender_service: Annotated[CalenderService, Depends()],
) -> ApiResponse:
    await calender_service.delete(calender_id)
    return ApiResponse()

@router.post("/list", response_model=ApiResponse, tags=["Calender"])
async def get_calender_post(
    page: int,
    calender_data: ListCalenderRequest,
    calender_service: Annotated[CalenderService, Depends()],
) -> ApiResponse:
    calenders = await calender_service.list(page, calender_data)
    return ApiResponse(
        data={"calenders": calenders}
    )