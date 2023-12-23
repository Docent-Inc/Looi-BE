import datetime
import json

from dateutil.relativedelta import relativedelta
from fastapi import Depends, HTTPException, status
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.core.security import get_current_user, check_length, time_now
from app.db.database import get_db, save_db
from app.db.models import User, Calendar
from app.core.aiRequset import GPTService
from app.schemas.request import CreateCalendarRequest, UpdateCalendarRequest, ListCalendarRequest
from app.service.abstract import AbstractDiaryService


class CalendarService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        self.user = user
        self.db = db

    async def create(self, calender_data: CreateCalendarRequest) -> Calendar:

        gpt_service = GPTService(self.user, self.db)
        if calender_data.start_time == "" or calender_data.end_time == "":
            schedule = await gpt_service.send_gpt_request(6, calender_data.content)
            schedule = json.loads(schedule)
            try:
                calender = Calendar(
                    User_id=self.user.id,
                    title=schedule['title'],
                    start_time=schedule['start_time'],
                    end_time=schedule['end_time'],
                    content=schedule['description'],
                    create_date=await time_now(),
                )
                save_db(calender, self.db)
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4014
                )
            return calender

        # 잘못된 날짜 입력시 예외처리
        if calender_data.start_time >= calender_data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4022,
            )

        # 제목이 없을 경우 자동 생성
        if calender_data.title == "":
            calender_data.title = await gpt_service.send_gpt_request(9, calender_data.content)

        # db에 저장
        await check_length(text=calender_data.title, max_length=255, error_code=4023)
        await check_length(text=calender_data.content, max_length=255, error_code=4023)
        now = await time_now()
        calender = Calendar(
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

    async def read(self, calender_id: int) -> Calendar:

        # 캘린더 조회
        calender = self.db.query(Calendar).filter(Calendar.id == calender_id, Calendar.User_id == self.user.id, Calender.is_deleted == False).first()

        # 캘린더가 없을 경우 예외 처리
        if not calender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4015,
            )

        # 캘린더 반환
        return calender

    async def update(self, calender_id: int, calender_data: UpdateCalendarRequest) -> Calendar:

        # 캘린더 조회
        calender = self.db.query(Calendar).filter(Calendar.id == calender_id, Calendar.User_id == self.user.id, Calendar.is_deleted == False).first()

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
        calender = self.db.query(Calendar).filter(Calendar.id == calender_id, Calendar.User_id == self.user.id, Calender.is_deleted == False).first()

        # 캘린더가 없을 경우 예외 처리
        if not calender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4015,
            )

        # 캘린더 삭제
        calender.is_deleted = True
        save_db(calender, self.db)

    async def list(self, year: int, month: int, day: int) -> list:

        # day가 0일 경우 월간 캘린더 조회
        if day == 0:
            start_of_month = datetime.datetime(year, month, 1)
            end_of_month = start_of_month + relativedelta(months=1)

            calendars = self.db.query(Calendar).filter(
                Calendar.User_id == self.user.id,
                Calendar.is_deleted == False,
                or_(
                    Calendar.start_time.between(start_of_month, end_of_month),
                    Calendar.end_time.between(start_of_month, end_of_month)
                )
            ).order_by(Calendar.start_time).all()
        # day가 0이 아닐 경우 일간 캘린더 조회
        else:
            start_of_day = datetime.datetime(year, month, day)
            end_of_day = start_of_day + datetime.timedelta(days=1)
            calendars = self.db.query(Calendar).filter(
                Calendar.User_id == self.user.id,
                Calendar.is_deleted == False,
                or_(
                    and_(Calendar.start_time >= start_of_day, Calendar.start_time < end_of_day),
                    and_(Calendar.end_time > start_of_day, Calendar.end_time <= end_of_day),
                    and_(Calendar.start_time <= start_of_day, Calendar.end_time >= end_of_day)
                )
            ).order_by(Calendar.start_time).all()

        return {"list": calendars}
