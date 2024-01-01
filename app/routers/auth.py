from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.response import ApiResponse
from app.schemas.request import TokenRefresh, UserUpdateRequest, PushUpdateRequest
from app.core.security import get_current_user, get_update_user
from app.service.auth import AuthService

router = APIRouter(prefix="/auth")

@router.get("/login/{service}/{env}", response_model=ApiResponse, tags=["Auth"])
async def get_auth_login(
    service: str,
    env: str,
    auth_service: Annotated[AuthService, Depends()]
):
    return ApiResponse(
        data={"url": await auth_service.login(service, env)}
    )

@router.get("/callback/{service}/{env}", response_model=ApiResponse, tags=["Auth"])
async def get_auth_callback(
    service: str,
    env: str,
    code: str,
    auth_service: Annotated[AuthService, Depends()]
):
    return ApiResponse(
        data=await auth_service.callback(service, env, code)
    )

@router.post("/refresh", response_model=ApiResponse, tags=["Auth"])
async def get_auth_refresh(
    token_refresh: TokenRefresh,
    auth_service: Annotated[AuthService, Depends()]
):
    return ApiResponse(
        data=await auth_service.refresh(token_refresh.refresh_token)
    )

@router.get("/info", response_model=ApiResponse, tags=["Auth"])
async def get_auth_info(
    current_user: Annotated[get_current_user, Depends()],
    auth_service: Annotated[AuthService, Depends()]
):
    return ApiResponse(
        data=await auth_service.info(current_user)
    )

@router.patch("/update", response_model=ApiResponse, tags=["Auth"])
async def patch_auth_update(
    auth_data: UserUpdateRequest,
    current_user: Annotated[get_update_user, Depends()],
    auth_service: Annotated[AuthService, Depends()]
):
    await auth_service.update(auth_data, current_user)
    return ApiResponse()

@router.patch("/update/push", response_model=ApiResponse, tags=["Auth"])
async def patch_auth_update_push(
    auth_data: PushUpdateRequest,
    current_user: Annotated[get_update_user, Depends()],
    auth_service: Annotated[AuthService, Depends()]
):
    await auth_service.update_push(auth_data, current_user)
    return ApiResponse()

@router.delete("/delete", response_model=ApiResponse, tags=["Auth"])
async def delete_auth_delete(
    current_user: Annotated[get_update_user, Depends()],
    auth_service: Annotated[AuthService, Depends()]
):
    await auth_service.delete(current_user)
    return ApiResponse()