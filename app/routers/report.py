from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.response import ApiResponse
from app.service.report import ReportService

router = APIRouter(prefix="/report")

@router.get("/{id}", tags=["Report"])
async def get_report_read(
    id: int,
    report_service: Annotated[ReportService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await report_service.read(id)
    )

@router.get("/list/{page}", tags=["Report"])
async def get_report_list(
    page: int,
    report_service: Annotated[ReportService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await report_service.list(page)
    )

@router.post("/create", tags=["Report"])
async def post_report_create(
    report_service: Annotated[ReportService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await report_service.generate()
    )