from fastapi import APIRouter
from app.gptapi.chatGPT import generate_text
from app.schemas.gpt import GPTResponse
from app.schemas.common import ApiResponse

router = APIRouter()
@router.get("/{text}", response_model=ApiResponse, tags=["gpt"])
async def get_gpt_result(text: str) -> GPTResponse:
    dream_name, dream, dream_resolution, today_luck, dream_image_url = await generate_text(text)

    return ApiResponse(
        success=True,
        data=GPTResponse(
            dream_name=dream_name,
            dream=dream,
            dream_resolution=dream_resolution,
            today_luck=today_luck,
            image_url=dream_image_url
        )
    )
