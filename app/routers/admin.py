from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/admin")

@router.get("/user/info", response_model=ApiResponse, tags=["Admin"])
async def get_user_info(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user_id:
        user_id = current_user.id

    if current_user.is_admin == True or current_user.id == user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.hashed_password = None
            return ApiResponse(data=user)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4401,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4401,
        )


