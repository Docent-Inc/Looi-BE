from fastapi import APIRouter, Depends
from app.feature.diary import create_night_diary, create_morning_diary, read_morning_diary, read_night_diary, \
    update_morning_diary, delete_morning_diary, update_night_diary, delete_night_diary, create_memo, list_morning_diary, \
    list_night_diary, create_calender, update_calender, read_calender, delete_calender, dairy_list, read_memo, \
    dairy_list_calender, get_diary_ratio, delete_memo
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.schemas.request import CreateDiaryRequest, UpdateDiaryRequest, CalenderRequest, MemoRequest, ListRequest, \
    CalenderListRequest
from app.schemas.response import User, ApiResponse

router = APIRouter(prefix="/diary")

@router.post("/morning/create", response_model=ApiResponse, tags=["Diary"])
async def morning_create(
    body: CreateDiaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
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
    await delete_morning_diary(diary_id, current_user, db)
    return ApiResponse()

@router.get("/morning/list", response_model=ApiResponse, tags=["Diary"])
async def morning_list(
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
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
    diary_id = await create_night_diary(body.content, current_user, db)
    return ApiResponse(
        data={"id": diary_id}
    )

@router.get("/night/read", response_model=ApiResponse, tags=["Diary"])
async def night_read(
    diary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
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
    await delete_night_diary(diary_id, current_user, db)
    return ApiResponse()

@router.get("/night/list", response_model=ApiResponse, tags=["Diary"])
async def night_list(
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    diaries = await list_night_diary(page, current_user, db)
    return ApiResponse(
        data={"diaries": diaries}
    )
'''
memo diary crud
'''
@router.post("/memo/create", response_model=ApiResponse, tags=["Memo"])
async def memo_create(
    body: MemoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    memo_id = await create_memo(body.content, current_user, db)
    return ApiResponse(
        data={"id": memo_id}
    )

@router.get("/memo/read", response_model=ApiResponse, tags=["Memo"])
async def memo_read(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    memo = await read_memo(memo_id, current_user, db)
    return ApiResponse(
        data={"memo": memo}
    )

# @router.post("/memo/update", response_model=ApiResponse, tags=["Memo"])
# async def memo_update(
#     body: MemoRequest,
#     memo_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ) -> ApiResponse:
#     '''
#     메모 수정 API, 사용자가 입력한 텍스트를 기반으로 메모를 수정합니다.
#
#     :param body: 사용자가 입력한 텍스트
#     :param memo_id: 수정할 메모의 id
#     :param current_user: 로그인한 사용자의 정보를 가져오는 의존성 주입
#     :param db: 데이터베이스 세션을 가져오는 의존성 주입
#     :return 메모 수정 결과
#     '''
#     memo_id = await update_memo(memo_id, body.content, current_user, db)
#     return ApiResponse(
#         data={"id": memo_id}
#     )

@router.delete("/memo/delete", response_model=ApiResponse, tags=["Memo"])
async def memo_delete(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    await delete_memo(memo_id, current_user, db)
    return ApiResponse()
'''
calender diary crud
'''
@router.post("/calender/create", response_model=ApiResponse, tags=["Calender"])
async def calender_create(
    body: CalenderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    calender_id = await create_calender(body, current_user, db)
    return ApiResponse(
        data={"id": calender_id}
    )

@router.get("/calender/read", response_model=ApiResponse, tags=["Calender"])
async def calender_read(
    calender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    calender = await read_calender(calender_id, current_user, db)
    return ApiResponse(
        data={"calender": calender}
    )

@router.put("/calender/update", response_model=ApiResponse, tags=["Calender"])
async def calender_update(
    body: CalenderRequest,
    calender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    calender_id = await update_calender(calender_id, body, current_user, db)
    return ApiResponse(
        data={"id": calender_id}
    )

@router.delete("/calender/delete", response_model=ApiResponse, tags=["Calender"])
async def calender_delete(
    calender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    await delete_calender(calender_id, current_user, db)
    return ApiResponse()

@router.post("/list", response_model=ApiResponse, tags=["Diary"])
async def list(
    list_request: ListRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    data = await dairy_list(list_request, current_user, db)
    return ApiResponse(data=data)

@router.post("/list/calender", response_model=ApiResponse, tags=["Calender"])
async def list_calender(
    list_request: CalenderListRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    data = await dairy_list_calender(list_request, current_user, db)
    return ApiResponse(
        data={
            "list": data
        }
    )

@router.get("/ratio", response_model=ApiResponse, tags=["Diary"])
async def get_ratio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    ratio = await get_diary_ratio(current_user, db)
    return ApiResponse(
        data={"ratio": ratio}
    )
