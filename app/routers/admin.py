from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.response import ApiResponse
from app.service.admin import AdminService

router = APIRouter(prefix="/admin")

@router.get("/user_list", response_model=ApiResponse, tags=["Admin"])
async def get_admin_user_list(
    admin_service: Annotated[AdminService, Depends()],
) -> ApiResponse:
    return ApiResponse(data=await admin_service.user_list())

@router.get("/dashboard", response_model=ApiResponse, tags=["Admin"])
async def get_admin_dashboard(
    admin_service: Annotated[AdminService, Depends()],
) -> ApiResponse:
    return ApiResponse(data=await admin_service.dashboard())

@router.get("/user_text", response_model=ApiResponse, tags=["Admin"])
async def get_admin_user_text(
    admin_service: Annotated[AdminService, Depends()],
) -> ApiResponse:
    return ApiResponse(data=await admin_service.user_text())