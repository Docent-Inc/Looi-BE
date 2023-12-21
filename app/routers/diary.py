from fastapi import APIRouter, Depends

from app.db.models import Memo
from app.feature.diary import create_night_diary, create_morning_diary, read_morning_diary, read_night_diary, \
    update_morning_diary, delete_morning_diary, update_night_diary, delete_night_diary, create_memo, list_morning_diary, \
    list_night_diary, create_calender, update_calender, read_calender, delete_calender, dairy_list, read_memo, \
    dairy_list_calender, get_diary_ratio, delete_memo, share_read_morning_diary, share_read_night_diary, update_memo
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.schemas.request import CreateDiaryRequest, UpdateDiaryRequest, CalenderRequest, MemoRequest, ListRequest, \
    CalenderListRequest, CreateNightDiaryRequest
from app.schemas.response import User, ApiResponse, ListResponse

router = APIRouter(prefix="/diary")

@router.post("/morning/create", response_model=ApiResponse, tags=["Diary"])
async def morning_create(
    body: CreateDiaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    diary = await create_morning_diary(body.content, current_user, db)
    return ApiResponse(
        data={"diary": diary}
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
    diary = await update_morning_diary(diary_id, body, current_user, db)
    return ApiResponse(
        data={"diary": diary}
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
    body: CreateNightDiaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    diary = await create_night_diary(body, current_user, db)
    return ApiResponse(
        data={"diary": diary}
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
    diary = await update_night_diary(diary_id, body, current_user, db)
    return ApiResponse(
        data={"diary": diary}
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
memo  crud
'''
@router.post("/memo/create", response_model=ApiResponse, tags=["Memo"])
async def post_memo_create(
    memo: Memo = Depends(create_memo)
) -> ApiResponse:
    return ApiResponse(
        data={"memo": memo}
    )

@router.get("/memo/read", response_model=ApiResponse, tags=["Memo"])
async def get_memo_read(
    memo: Memo = Depends(read_memo)
) -> ApiResponse:
    return ApiResponse(
        data={"memo": memo}
    )

@router.post("/memo/update", response_model=ApiResponse, tags=["Memo"])
async def post_memo_update(
    memo: Memo = Depends(update_memo)
) -> ApiResponse:
    return ApiResponse(
        data={"memo": memo}
    )

@router.delete("/memo/delete", response_model=ApiResponse, tags=["Memo"])
async def delete_memo_delete(
    memo: Memo = Depends(delete_memo)
) -> ApiResponse:
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
    calender = await create_calender(body, current_user, db)
    return ApiResponse(
        data={"calender": calender}
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

@router.post("/calender/update", response_model=ApiResponse, tags=["Calender"])
async def calender_update(
    body: CalenderRequest,
    calender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    calender = await update_calender(calender_id, body, current_user, db)
    return ApiResponse(
        data={"calender": calender}
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

    # request type에 따라 diary list를 가져옴
    all_items, count, total_count = await dairy_list(list_request, current_user, db)

    # 가져온 diary list를 response 형태로 변환
    return ApiResponse(
        data=ListResponse(
            list=all_items,
            count=count,
            total_count=total_count,
        )
    )

@router.post("/list/calender", response_model=ApiResponse, tags=["Calender"])
async def list_calender(
    list_request: CalenderListRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    today_count, data = await dairy_list_calender(list_request, current_user, db)
    return ApiResponse(
        data={
            "today_count": today_count,
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

@router.get("/morning/share/{diary_id}", response_model=ApiResponse, tags=["Diary"])
async def share_morning_diary(
    diary_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    diary = await share_read_morning_diary(diary_id, db)
    return ApiResponse(
        data={"diary": diary}
    )

@router.get("/night/share/{diary_id}", response_model=ApiResponse, tags=["Diary"])
async def share_night_diary(
    diary_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    diary = await share_read_night_diary(diary_id, db)
    return ApiResponse(
        data={"diary": diary}
    )
