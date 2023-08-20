from fastapi import APIRouter, Depends

from app.feature.diary import create_night_diary, create_morning_diary, read_morning_diary, read_night_diary
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.schemas.request import CreateDiaryRequest
from app.schemas.response import User, ApiResponse

router = APIRouter(prefix="/diary")

@router.post("/morning/create", response_model=ApiResponse, tags=["Diary"])
async def morning_create(
    body: CreateDiaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    아침 일기 생성 API, 사용자가 입력한 텍스트를 기반으로 아침 일기를 생성합니다.

    :param body: 사용자가 입력한 텍스트
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 아침 일기 생성 결과
    '''
    diary_id = await create_morning_diary(body.image_model, body.content, current_user, db)
    return ApiResponse(
        data={"id": diary_id}
    )

@router.get("/morning/read", response_model=ApiResponse, tags=["Diary"])
async def morning_read(
    diary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    아침 일기 조회 API, 사용자가 입력한 텍스트를 기반으로 아침 일기를 조회합니다.

    :param body: 사용자가 입력한 텍스트
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 아침 일기 조회 결과
    '''
    diary = await read_morning_diary(diary_id, current_user, db)
    return ApiResponse(
        data={"diary": diary}
    )

@router.post("/night/create", response_model=ApiResponse, tags=["Diary"])
async def night_create(
    body: CreateDiaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    저녁 일기 생성 API, 사용자가 입력한 텍스트를 기반으로 저녁 일기를 생성합니다.

    :param body: 사용자가 입력한 텍스트
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 저녁 일기 생성 결과
    '''

    diary_id = await create_night_diary(body.image_model, body.content, current_user, db)
    return ApiResponse(
        data={"id": diary_id}
    )

@router.get("/night/read", response_model=ApiResponse, tags=["Diary"])
async def night_read(
    diary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    저녁 일기 조회 API, 사용자가 입력한 텍스트를 기반으로 저녁 일기를 조회합니다.

    :param body: 사용자가 입력한 텍스트
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 저녁 일기 조회 결과
    '''
    diary = await read_night_diary(diary_id, current_user, db)
    return ApiResponse(
        data={"diary": diary}
    )