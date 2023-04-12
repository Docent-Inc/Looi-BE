from fastapi import APIRouter
from app.gptapi.chatGPT import generate_text
from app.schemas.gpt import GPTResponse
from app.schemas.common import ApiResponse
from pydantic import BaseModel
from fastapi import Request
from fastapi import Cookie, Response
from typing import Optional
import uuid
from fastapi.responses import JSONResponse


from sqlalchemy import create_engine
from app.models.test import Dream
from sqlalchemy.orm import declarative_base, sessionmaker
DB_URL = 'mysql+pymysql://dmz:1234@swiftsjh.tplinkdns.com:3306/BMSM'
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

router = APIRouter(prefix="/gpt")
@router.get("/{text}", response_model=ApiResponse, tags=["gpt"])
async def get_gpt_result(text: str, user_cookie: Optional[str] = Cookie(None)) -> GPTResponse:
    dream_name, dream, dream_resolution, today_luck, dream_image_url = await generate_text(text, user_cookie)

    if user_cookie is None:
        user_cookie = str(uuid.uuid4())  # 새로운 고유한 ID 생성

    response_data = ApiResponse(
        success=True,
        data=GPTResponse(
            dream_name=dream_name,
            dream=dream,
            dream_resolution=dream_resolution,
            today_luck=today_luck,
            image_url=dream_image_url
        )
    )

    response = JSONResponse(content=response_data.dict())

    if not user_cookie:
        response.set_cookie(key="user_cookie", value=user_cookie, max_age=60 * 60 * 24 * 30)  # 쿠키를 30일 동안 유지

    print(user_cookie)

    return response

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