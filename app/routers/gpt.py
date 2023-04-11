from fastapi import APIRouter
from app.gptapi.chatGPT import generate_text
from app.schemas.gpt import GPTResponse
from app.schemas.common import ApiResponse
from pydantic import BaseModel

from sqlalchemy import create_engine
from app.models.test import Dream
from sqlalchemy.orm import declarative_base, sessionmaker
DB_URL = 'mysql+pymysql://dmz:1234@swiftsjh.tplinkdns.com:3306/BMSM'
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

router = APIRouter(prefix="/gpt")
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

class PhoneNumberData(BaseModel):
    phoneNumber: str
    dreamName: str

@router.post("/test", response_model=ApiResponse, tags=["gpt"])
async def test(data: PhoneNumberData):
    session = SessionLocal()
    new_entry = Dream(phone=data.phoneNumber, dreamName=data.dreamName)

    try:
        session.add(new_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        return ApiResponse(success=False, data=False)
    finally:
        session.close()
    return ApiResponse(success=True, data=True)