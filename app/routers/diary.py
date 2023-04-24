from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.common import ApiResponse
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.schemas.response.user import User
from app.schemas.request.crud import Create
from app.crud.diary import createDiary
router = APIRouter(prefix="/diary")

@router.post("/create", response_model=ApiResponse, tags=["Diary"])
async def create_diary(
    create: Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    diary = await createDiary(create, current_user.id, db)
    if diary == True:
        return ApiResponse(
            success=True,
            data="꿈 일기가 성공적으로 작성되었습니다."
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="꿈 일기 작성에 실패하였습니다.")