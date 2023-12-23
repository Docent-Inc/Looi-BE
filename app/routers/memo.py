from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.request import CreateMemoRequest, UpdateMemoRequest
from app.schemas.response import ApiResponse
from app.service.memo import MemoService

router = APIRouter(prefix="/memo")

@router.post("/create", response_model=ApiResponse, tags=["Memo"])
async def post_memo_create(
    memo_data: CreateMemoRequest,
    memo_service: Annotated[MemoService, Depends()],
) -> ApiResponse:
    memo = await memo_service.create(memo_data)
    return ApiResponse(
        data={"memo": memo}
    )

@router.get("/read", response_model=ApiResponse, tags=["Memo"])
async def get_memo_read(
    memo_id: int,
    memo_service: Annotated[MemoService, Depends()],
) -> ApiResponse:
    memo = await memo_service.read(memo_id)
    return ApiResponse(
        data={"memo": memo}
    )

@router.patch("/update", response_model=ApiResponse, tags=["Memo"])
async def post_memo_update(
    memo_id: int,
    memo_data: UpdateMemoRequest,
    memo_service: Annotated[MemoService, Depends()],
) -> ApiResponse:
    memo = await memo_service.update(memo_id, memo_data)
    return ApiResponse(
        data={"memo": memo}
    )

@router.delete("/delete", response_model=ApiResponse, tags=["Memo"])
async def delete_memo_delete(
    memo_service: Annotated[MemoService, Depends()],
) -> ApiResponse:
    await memo_service.delete()
    return ApiResponse()

@router.get("/list", response_model=ApiResponse, tags=["Memo"])
async def get_memo_list(
    page: int,
    memo_service: Annotated[MemoService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await memo_service.list(page)
    )