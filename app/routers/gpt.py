from fastapi import APIRouter
from pydantic import BaseModel
from app.chatGPT import generate_text
from app.db.dream import create_table
class GPTResponse(BaseModel):
    dream_name: str
    dream: str
    dream_resolution: str
    today_luck: str
    image_url: str

router = APIRouter()
@router.get("/{text}", response_model=GPTResponse)
async def get_gpt_result(text: str) -> GPTResponse:
    create_table()
    dream_name, dream, dream_resolution, today_luck, dream_image_url = await generate_text(text)
    return GPTResponse(
        dream_name=dream_name,
        dream=dream,
        dream_resolution=dream_resolution,
        today_luck=today_luck,
        image_url=dream_image_url
    )
