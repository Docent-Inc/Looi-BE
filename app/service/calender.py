import datetime

from dateutil.relativedelta import relativedelta
from fastapi import Depends, HTTPException, status
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.core.security import get_current_user, check_length, time_now
from app.db.database import get_db, save_db
from app.db.models import User, Calender
from app.feature.aiRequset import GPTService
from app.schemas.request import CreateCalenderRequest, UpdateCalenderRequest, ListCalenderRequest
from app.service.abstract import AbstractDiaryService


class CalenderService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        self.user = user
        self.db = db

    async def create(self, calender_data: CreateCalenderRequest) -> Calender:

        # 잘못된 날짜 입력시 예외처리
        if calender_data.start_time >= calender_data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4022,
            )

        # 제목이 없을 경우 자동 생성
        if calender_data.title == "":
            gpt_service = GPTService(self.user, self.db)
            calender_data.title = await gpt_service.send_gpt_request(9, calender_data.content)

        # db에 저장
        await check_length(text=calender_data.title, max_length=255, error_code=4023)
        await check_length(text=calender_data.content, max_length=255, error_code=4023)
        now = await time_now()
        calender = Calender(
            User_id=self.user.id,
            start_time=calender_data.start_time,
            end_time=calender_data.end_time,
            title=calender_data.title,
            content=calender_data.content,
            create_date=now,
        )
        calender = save_db(calender, self.db)

        # 캘린더 반환
        return calender

    async def read(self, calender_id: int) -> Calender:

        # 캘린더 조회
        calender = self.db.query(Calender).filter(Calender.id == calender_id, Calender.User_id == self.user.id, Calender.is_deleted == False).first()

        # 캘린더가 없을 경우 예외 처리
        if not calender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4015,
            )

        # 캘린더 반환
        return calender

    async def update(self, calender_id: int, calender_data: UpdateCalenderRequest) -> Calender:

        # 캘린더 조회
        calender = self.db.query(Calender).filter(Calender.id == calender_id, Calender.User_id == self.user.id, Calender.is_deleted == False).first()

        # 캘린더가 없을 경우 예외 처리
        if not calender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4015,
            )

        # 캘린더 수정
        if calender_data.title != "":
            await check_length(text=calender_data.title, max_length=255, error_code=4023)
            calender.title = calender_data.title
        if calender_data.content != "":
            await check_length(text=calender_data.content, max_length=255, error_code=4023)
            calender.content = calender_data.content
        if calender_data.start_time != "" and calender_data.end_time != "":
            if calender_data.start_time >= calender_data.end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4022,
                )
            calender.start_time = calender_data.start_time
            calender.end_time = calender_data.end_time
        elif calender_data.start_time != "":
            if calender_data.start_time >= calender.end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4022,
                )
            calender.start_time = calender_data.start_time
        elif calender_data.end_time != "":
            if calender.start_time >= calender_data.end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4022,
                )
            calender.end_time = calender_data.end_time

        calender = save_db(calender, self.db)

        return calender

    async def delete(self, calender_id: int) -> None:

        # 캘린더 조회
        calender = self.db.query(Calender).filter(Calender.id == calender_id, Calender.User_id == self.user.id, Calender.is_deleted == False).first()

        # 캘린더가 없을 경우 예외 처리
        if not calender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4015,
            )

        # 캘린더 삭제
        calender.is_deleted = True
        save_db(calender, self.db)

    async def list(self, page: int, calender_data: ListCalenderRequest) -> list:

        # day가 0일 경우 월간 캘린더 조회
        if calender_data.day == 0:
            year = calender_data.year
            month = calender_data.month
            start_of_month = datetime.datetime(year, month, 1)
            end_of_month = start_of_month + relativedelta(months=1)

            calenders = self.db.query(Calender).filter(
                Calender.User_id == self.user.id,
                Calender.is_deleted == False,
                or_(
                    Calender.start_time.between(start_of_month, end_of_month),
                    Calender.end_time.between(start_of_month, end_of_month)
                )
            ).order_by(Calender.start_time).all()
        # day가 0이 아닐 경우 일간 캘린더 조회
        else:
            year = calender_data.year
            month = calender_data.month
            day = calender_data.day
            start_of_day = datetime.datetime(year, month, day)
            end_of_day = start_of_day + datetime.timedelta(days=1)
            calenders = self.db.query(Calender).filter(
                Calender.User_id == self.user.id,
                Calender.is_deleted == False,
                or_(
                    and_(Calender.start_time >= start_of_day, Calender.start_time < end_of_day),
                    and_(Calender.end_time > start_of_day, Calender.end_time <= end_of_day),
                    and_(Calender.start_time <= start_of_day, Calender.end_time >= end_of_day)
                )
            ).order_by(Calender.start_time).all()

        return calenders