from fastapi import APIRouter, Depends, HTTPException, status
from app.gptapi.generateDream import generate_text
from app.schemas.response.gpt import BasicResponse, ImageResponse, CheckListResponse
from app.schemas.common import ApiResponse
from app.gptapi.generateImg import generate_img
from app.gptapi.generateCheckList import generate_checklist
from app.core.security import get_current_user
from app.schemas.response.user import User
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.db.models.dream import DreamText, DreamImage
router = APIRouter(prefix="/generate")

async def get_text_data(textId: int, user_id: int, db: Session):
    # 데이터베이스에서 textId와 user_id를 사용하여 데이터를 검색하는 코드를 작성하세요.
    text_data = db.query(DreamText).filter(DreamText.id == textId, DreamText.User_id == user_id).first()
    # 쿼리를 실행한 후, 해당하는 데이터가 없으면 None을 반환하고, 데이터가 있으면 해당 데이터를 반환하세요.
    return text_data

@router.post("/dream", response_model=ApiResponse, tags=["Generate"])
async def generate_basic(
    text: str, # 사용자가 입력한 텍스트
    db: Session = Depends(get_db), # 데이터베이스 세션
    current_user: User = Depends(get_current_user), # 로그인한 사용자의 정보
) -> BasicResponse:
    dream_name, dream, dream_image_url = await generate_text(text, current_user.id, db)
    return ApiResponse(
        success=True,
        data=BasicResponse(
            dream_name=dream_name,
            dream=dream,
            image_url=dream_image_url
        )
    )

@router.post("/image", response_model=ApiResponse, tags=["Generate"])
async def generate_image(
    textId: int, # 생성된 꿈 텍스트의 id
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImageResponse:

    # 데이터베이스에서 textId와 current_user.id를 확인 후 prompt 가져오기
    # TODO : 생성된 이미지의 갯수 확인 후 제한 걸기
    text_data = await get_text_data(textId, current_user.id, db)
    if text_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="생성된 꿈이 없습니다.")

    prompt = text_data.DALLE2 # 생성된 DALLE2 프롬프트 정보 불러오기
    dream_image_url = await generate_img(prompt, current_user.id)
    # 데이터베이스에 dream_image_url 저장
    dream_image = DreamImage(
        Text_id=textId,
        dream_image_url=dream_image_url
    )
    db.add(dream_image)
    db.commit()
    db.refresh(dream_image)
    return ApiResponse(
        success=True,
        data=ImageResponse(
            image_url=dream_image_url
        )
    )

@router.post("/checklist", response_model=ApiResponse, tags=["Generate"])
async def generate_image(
    textId: int, # 생성된 꿈 텍스트의 id
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImageResponse:

    # 데이터베이스에서 textId와 current_user.id를 확인 후 dream 가져오기
    text_data = await get_text_data(textId, current_user.id, db)
    if text_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="생성된 꿈이 없습니다.")

    dream = text_data.dream # 생성된 꿈 정보 불러오기
    dream_resolution, today_checklist = await generate_checklist(textId, dream, db)
    return ApiResponse(
        success=True,
        data=CheckListResponse(
            dream_resolution=dream_resolution,
            today_checklist=today_checklist
        )
    )