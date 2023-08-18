from fastapi import APIRouter, Depends
from app.feature.generate_kr import generate_text, generate_resolution_clova, generate_image_model
from app.schemas.response.gpt import BasicResponse, ResolutionResponse
from app.schemas.request.generate import Generate, Resolution, ImageRequest
from app.schemas.common import ApiResponse
from app.core.security import get_current_user
from app.schemas.response.user import User
from app.db.database import get_db
from sqlalchemy.orm import Session
router = APIRouter(prefix="/generate")

@router.post("/image", response_model=ApiResponse, tags=["Generate"])
async def generate_image(
    body: ImageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    '''
    이미지 생성 API, 사용자가 입력한 텍스트를 기반으로 이미지를 생성합니다.
    '''
    iamge_url = await generate_image_model(body.image_model, body.text)
    return ApiResponse(
        success=True,
        data=iamge_url
    )

@router.post("/dream", response_model=ApiResponse, tags=["Generate"])
async def generate_basic(
    generte: Generate, # 사용자가 입력한 텍스트
    db: Session = Depends(get_db), # 데이터베이스 세션
    current_user: User = Depends(get_current_user), # 로그인한 사용자의 정보
) -> BasicResponse:
    '''
    꿈 텍스트 생성 API, 사용자가 입력한 텍스트를 기반으로 꿈 제목과 이미지를 생성합니다.

    :param generte: 사용자가 입력한 텍스트
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :return: 꿈 텍스트 생성 결과
    '''
    id, dream_name, dream, dream_image_url = await generate_text(generte.image_model, generte.text, current_user.id, db)
    return ApiResponse(
        success=True,
        data=BasicResponse(
            id=id,
            dream_name=dream_name,
            dream=dream,
            image_url=dream_image_url
        )
    )



@router.post("/resolution", response_model=ApiResponse, tags=["Generate"])
async def resolution(
    text: Resolution,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResolutionResponse:
    '''
    꿈 해몽 생성 API, 사용자가 입력한 텍스트를 기반으로 꿈 해몽을 생성합니다.

    :param text: 사용자가 입력한 텍스트
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :return: 꿈 해몽 생성 결과
    '''
    dream_resolution = await generate_resolution_clova(text.text, db)
    return ApiResponse(
        success=True,
        data=ResolutionResponse(
            dream_resolution=dream_resolution
        )
)