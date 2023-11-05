from fastapi import APIRouter, Depends

from app.core.apiDetail import ApiDetail
from app.core.security import get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session

from app.feature.report import read_report, list_report
from app.schemas.response import ApiResponse, User

router = APIRouter(prefix="/report")

@router.get("/{id}", tags=["Report"])
async def get_report(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    report = await read_report(id, current_user, db)
    return ApiResponse(
        data=report
    )
get_report.__doc__ = f"[API detail]({ApiDetail.get_report})"

@router.get("/list/{page}", tags=["Report"])
async def get_report_list(
    page: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    report_list = await list_report(page, current_user, db)
    return ApiResponse(
        data=report_list
    )
get_report_list.__doc__ = f"[API detail]({ApiDetail.get_report_list})"

