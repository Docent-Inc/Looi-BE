from fastapi import APIRouter, Depends

from app.feature.diary import create_night_diary, create_morning_diary, read_morning_diary, read_night_diary, \
    update_morning_diary, delete_morning_diary, update_night_diary, delete_night_diary, create_memo, list_morning_diary, \
    list_night_diary, create_calender
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.schemas.request import CreateDiaryRequest, UpdateDiaryRequest, CreateMemoRequest, CalenderRequest
from app.schemas.response import User, ApiResponse

router = APIRouter(prefix="/diary")

'''
moring diary crud
'''
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
    diary_id = await create_morning_diary(body.content, current_user, db)
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

@router.post("/morning/update", response_model=ApiResponse, tags=["Diary"])
async def morning_update(
    body: UpdateDiaryRequest,
    diary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    아침 일기 수정 API, 사용자가 입력한 텍스트를 기반으로 아침 일기를 수정합니다.

    :param body: 사용자가 입력한 텍스트
    :param diary_id: 수정할 일기의 id
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 아침 일기 수정 결과
    '''
    diary_id = await update_morning_diary(diary_id, body, current_user, db)
    return ApiResponse(
        data={"id": diary_id}
    )

@router.delete("/morning/delete", response_model=ApiResponse, tags=["Diary"])
async def morning_delete(
    diary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    아침 일기 삭제 API, 사용자가 입력한 텍스트를 기반으로 아침 일기를 삭제합니다.

    :param diary_id: 삭제할 일기의 id
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 아침 일기 삭제 결과
    '''
    await delete_morning_diary(diary_id, current_user, db)
    return ApiResponse()

@router.get("/morning/list", response_model=ApiResponse, tags=["Diary"])
async def morning_list(
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    아침 일기 리스트 조회 API, 사용자가 입력한 텍스트를 기반으로 아침 일기 리스트를 조회합니다.

    :param page: 조회할 페이지 번호
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 아침 일기 리스트 조회 결과
    '''
    diaries = await list_morning_diary(page, current_user, db)
    return ApiResponse(
        data={"diaries": diaries}
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

    diary_id = await create_night_diary(body.content, current_user, db)
    return ApiResponse(
        data={"id": diary_id}
    )
'''
night diary crud
'''
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

@router.post("/night/update", response_model=ApiResponse, tags=["Diary"])
async def night_update(
    body: UpdateDiaryRequest,
    diary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    저녁 일기 수정 API, 사용자가 입력한 텍스트를 기반으로 저녁 일기를 수정합니다.

    :param body: 사용자가 입력한 텍스트
    :param diary_id: 수정할 일기의 id
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 저녁 일기 수정 결과
    '''
    diary_id = await update_night_diary(diary_id, body, current_user, db)
    return ApiResponse(
        data={"id": diary_id}
    )

@router.delete("/night/delete", response_model=ApiResponse, tags=["Diary"])
async def night_delete(
    diary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    저녁 일기 삭제 API, 사용자가 입력한 텍스트를 기반으로 저녁 일기를 삭제합니다.

    :param diary_id: 삭제할 일기의 id
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 저녁 일기 삭제 결과
    '''
    await delete_night_diary(diary_id, current_user, db)
    return ApiResponse()

@router.get("/night/list", response_model=ApiResponse, tags=["Diary"])
async def night_list(
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    저녁 일기 리스트 조회 API, 사용자가 입력한 텍스트를 기반으로 저녁 일기 리스트를 조회합니다.

    :param page: 조회할 페이지 번호
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return: 저녁 일기 리스트 조회 결과
    '''
    diaries = await list_night_diary(page, current_user, db)
    return ApiResponse(
        data={"diaries": diaries}
    )
'''
memo diary crud
'''
@router.post("/memo/create", response_model=ApiResponse, tags=["Memo"])
async def memo_create(
    body: CreateMemoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    메모 생성 API, 사용자가 입력한 텍스트를 기반으로 메모를 생성합니다.

    :param body: 사용자가 입력한 텍스트
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    :return 메모 생성 결과
    '''
    memo_id = await create_memo(body.content, current_user, db)
    return ApiResponse(
        data={"id": memo_id}
    )

# @router.get("/memo/read", response_model=ApiResponse, tags=["Memo"])
# async def memo_read(
#     memo_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ) -> ApiResponse:
#     '''
#     메모 조회 API, 사용자가 입력한 텍스트를 기반으로 메모를 조회합니다.
#
#     :param memo_id: 조회할 메모의 id
#     :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
#     :param db: 데이터베이스 세션을 가져오는 의존성 주입
#     '''
#     memo = await read_memo(memo_id, current_user, db)
#     return ApiResponse(
#         data={"memo": memo}
#     )

'''
calender diary crud
'''
@router.post("/calender/create", response_model=ApiResponse, tags=["Calender"])
async def calender_create(
    body: CalenderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    '''
    캘린더 생성 API, 사용자가 입력한 텍스트를 기반으로 캘린더를 생성합니다.

    :param body: 사용자가 입력한 텍스트
    :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
    :param db: 데이터베이스 세션을 가져오는 의존성 주입
    '''
    calender_id = await create_calender(body, current_user, db)
    return ApiResponse(
        data={"id": calender_id}
    )
