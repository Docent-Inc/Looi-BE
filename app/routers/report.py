from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session

from app.db.models import User
from app.feature.report import read_report, list_report, generate_report
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/report")

@router.post("/generate/{user_id}", tags=["Report"])
async def report(
    user_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    user = db.query(User).filter(User.id == user_id).first()
    report_id = await generate_report(user, db)
    return ApiResponse(
        data={"id": report_id}
    )

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

