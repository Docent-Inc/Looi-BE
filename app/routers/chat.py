from typing import Annotated
from fastapi import APIRouter, Depends, BackgroundTasks
from app.schemas.request import ChatRequest
from app.schemas.response import ApiResponse
from app.service.chat import ChatService

router = APIRouter(prefix="/chat")

@router.post("", tags=["Chat"])
async def chat(
    chat_data: ChatRequest,
    background_tasks: BackgroundTasks,
    chat_service: Annotated[ChatService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await chat_service.create(chat_data, background_tasks)
    )

@router.get("/welcome", tags=["Chat"])
async def get_welcome(
    type: int,
    chat_service: Annotated[ChatService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await chat_service.welcome(type)
    )

@router.get("/helper", tags=["Chat"])
async def get_helper(
    type: int,
    chat_service: Annotated[ChatService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await chat_service.helper(type)
    )