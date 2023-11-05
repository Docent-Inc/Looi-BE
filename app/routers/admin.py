from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core.security import get_current_user, get_current_user_is_admin
from app.db.database import get_db
from app.db.models import User, WelcomeChat, HelperChat
from app.schemas.request import WelcomeRequest, HelperRequest
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/admin")

@router.get("/user/info", response_model=ApiResponse, tags=["Admin"])
async def get_user_info(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.hashed_password = None
        return ApiResponse(data=user)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4401,
        )

@router.post("/welcome", response_model=ApiResponse, tags=["Admin"])
async def post_welcome(
    request: WelcomeRequest,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    new_data = WelcomeChat(
        text=request.text,
        type=request.type,
    )
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return ApiResponse()

@router.get("/welcome/list", response_model=ApiResponse, tags=["Admin"])
async def get_welcome_list(
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    data = db.query(WelcomeChat).filter(WelcomeChat.is_deleted==False).all()
    return ApiResponse(data=data)
@router.delete("/welcome", response_model=ApiResponse, tags=["Admin"])
async def delete_welcome(
    welcome_id: int,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    data = db.query(WelcomeChat).filter(WelcomeChat.id == welcome_id).first()
    db.delete(data)
    db.commit()
    return ApiResponse()

@router.post("/helper", response_model=ApiResponse, tags=["Admin"])
async def post_helper(
    request: HelperRequest,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    new_data = HelperChat(
        text=request.text,
        type=request.type,
    )
    db.add(new_data)
    db.commit()
    db.refresh(new_data)

    return ApiResponse()
@router.get("/helper/list", response_model=ApiResponse, tags=["Admin"])
async def get_helper_list(
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    data = db.query(HelperChat).filter(HelperChat.is_deleted==False).all()
    return ApiResponse(data=data)

@router.delete("/helper", response_model=ApiResponse, tags=["Admin"])
async def delete_helper(
    helper_id: int,
    current_user: User = Depends(get_current_user_is_admin),
    db: Session = Depends(get_db),
):
    data = db.query(HelperChat).filter(HelperChat.id == helper_id).first()
    db.delete(data)
    db.commit()
    return ApiResponse()
