from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import User, LookieChat
from app.schemas.request import LookieChatRequest
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/admin")

@router.get("/user/info", response_model=ApiResponse, tags=["Admin"])
async def get_user_info(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    [API detail](https://docs.google.com/spreadsheets/d/17lnN82TlJjLV46Fdh3mooUOFEw_R6EtDG6938KgIshA/edit#gid=531870320)
    """
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

@router.post("/lookie/chat", response_model=ApiResponse, tags=["Admin"])
async def lookie_chat(
    lookie_chat_request: LookieChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_admin == True:
        new_data = LookieChat(
            text=lookie_chat_request.text,
            type=lookie_chat_request.type,
        )
        db.add(new_data)
        db.commit()
        db.refresh(new_data)

        return ApiResponse()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4402,
        )

@router.get("/looki/chat/list", response_model=ApiResponse, tags=["Admin"])
async def lookie_chat(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_admin == True:
        data = db.query(LookieChat).filter(LookieChat.is_deleted==False).all()
        return ApiResponse(data=data)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4402,
        )

@router.delete("/looki/chat", response_model=ApiResponse, tags=["Admin"])
async def lookie_chat(
    lookie_chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_admin == True:
        data = db.query(LookieChat).filter(LookieChat.id == lookie_chat_id).first()
        db.delete(data)
        db.commit()
        return ApiResponse()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4402,
        )



