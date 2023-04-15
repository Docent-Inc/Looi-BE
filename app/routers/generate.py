from fastapi import APIRouter
from app.gptapi.generateDream import generate_text
from app.schemas.gpt import BasicResponse, ImageResponse
from app.schemas.common import ApiResponse
from app.gptapi.generateImg import create_img

router = APIRouter(prefix="/generate")
@router.post("/dream", response_model=ApiResponse, tags=["generate"])
async def generate_basic(text: str) -> BasicResponse:
    # TODO: 유저정보를 확인하는 로직 필요
    dream_name, dream, dream_resolution, today_luck, dream_image_url = await generate_text(text)
    return ApiResponse(
        success=True,
        data=BasicResponse(
            dream_name=dream_name,
            dream=dream,
            dream_resolution=dream_resolution,
            today_luck=today_luck,
            image_url=dream_image_url
        )
    )

@router.post("/image", response_model=ApiResponse, tags=["generate"])
async def generate_image(text: str) -> ImageResponse:
    # TODO: 유저정보를 확인하는 로직 필요
    dreamName = "이미지 이름"
    prompt = "gpt프롬프트"
    dream_image_url =  await create_img(dreamName, prompt)
    return ApiResponse(
        success=True,
        data=ImageResponse(
            image_url=dream_image_url
        )
    )
