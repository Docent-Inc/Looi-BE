from fastapi import APIRouter, Depends

from app.core.api_detail import ApiDetail
from app.feature.generate import generate_report, generate_luck
from app.core.security import get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.schemas.response import ApiResponse, User

router = APIRouter(prefix="/generate")

@router.get("/report", tags=["Generate"])
async def report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    report = await generate_report(current_user, db)
    return ApiResponse(
        data=report
    )

@router.get("/luck", tags=["Generate"])
async def luck(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    luck = await generate_luck(current_user, db)
    return ApiResponse(
        data={"luck": luck}
    )


report.__doc__ = f"[API detail]({ApiDetail.generate_report})"
luck.__doc__ = f"[API detail]({ApiDetail.generate_luck})"
