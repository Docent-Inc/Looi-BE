import json
from datetime import datetime, timedelta
import aioredis
from dateutil.relativedelta import relativedelta
from fastapi import Depends, HTTPException, status
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.core.security import get_current_user, check_length, time_now
from app.db.database import get_db, save_db, get_redis_client
from app.db.models import User, Calendar
from app.core.aiRequset import GPTService
from app.schemas.request import CreateCalendarRequest, UpdateCalendarRequest
from app.service.abstract import AbstractDiaryService


class CalendarService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db),
                 redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def create(self, calender_data: CreateCalendarRequest) -> Calendar:

        gpt_service = GPTService(self.user, self.db)
        if calender_data.start_time == "" or calender_data.end_time == "":
            schedule = await gpt_service.send_gpt_request(6, calender_data.content)
            schedule = json.loads(schedule)
            try:
                push_time = None
                if self.user.push_schedule:
                    push_time_delta = timedelta(minutes=self.user.push_schedule)
                    push_time = datetime.strptime(schedule['start_time'], '%Y-%m-%d %H:%M:%S') - push_time_delta
                calendar = Calendar(
                    User_id=self.user.id,
                    title=schedule['title'],
                    start_time=schedule['start_time'],
                    end_time=schedule['end_time'],
                    push_time=push_time,
                    content="",
                    create_date=await time_now(),
                )
                save_db(calendar, self.db)

                # list cache 삭제
                keys = await self.redis.keys(f"calendar:list:{self.user.id}:*")
                for key in keys:
                    await self.redis.delete(key)

                # today_calendar cache 삭제
                now = await time_now()
                redis_key = f"today_calendar_list:{self.user.id}:{now.day}"
                await self.redis.delete(redis_key)
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4014
                )
            return calendar

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
        calendar = Calendar(
            User_id=self.user.id,
            start_time=calender_data.start_time,
            end_time=calender_data.end_time,
            title=calender_data.title,
            content=calender_data.content,
            create_date=now,
        )
        calendar = save_db(calendar, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"calendar:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # today_calendar cache 삭제
        now = await time_now()
        redis_key = f"today_calendar_list:{self.user.id}:{now.day}"
        await self.redis.delete(redis_key)

        return calendar

    async def generate(self, id: int):
        pass

    async def read(self, calender_id: int) -> Calendar:

        # 캘린더 조회
        calender = self.db.query(Calendar).filter(Calendar.id == calender_id, Calendar.User_id == self.user.id, Calendar.is_deleted == False).first()

        # 캘린더가 없을 경우 예외 처리
        if not calender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4015,
            )

        # 캘린더 반환
        return calender

    async def update(self, calendar_id: int, calendar_data: UpdateCalendarRequest) -> Calendar:

        # 캘린더 조회
        calendar = self.db.query(Calendar).filter(Calendar.id == calendar_id, Calendar.User_id == self.user.id, Calendar.is_deleted == False).first()

        # 캘린더가 없을 경우 예외 처리
        if not calendar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4015,
            )

        # 캘린더 수정
        if calendar_data.title != "":
            await check_length(text=calendar_data.title, max_length=255, error_code=4023)
            calendar.title = calendar_data.title
        if calendar_data.content != "":
            await check_length(text=calendar_data.content, max_length=255, error_code=4023)
            calendar.content = calendar_data.content
        if calendar_data.start_time != "" and calendar_data.end_time != "":
            if calendar_data.start_time >= calendar_data.end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4022,
                )
            calendar.start_time = calendar_data.start_time
            calendar.end_time = calendar_data.end_time
        elif calendar_data.start_time != "":
            if calendar_data.start_time >= calendar.end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4022,
                )
            calendar.start_time = calendar_data.start_time
        elif calendar_data.end_time != "":
            if calendar.start_time >= calendar_data.end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4022,
                )
            calendar.end_time = calendar_data.end_time

        if self.user.push_schedule:
            push_time_delta = timedelta(minutes=self.user.push_schedule)
            push_time = datetime.strptime(calendar.start_time, '%Y-%m-%d %H:%M:%S') - push_time_delta
            calendar.push_time = push_time

        calendar = save_db(calendar, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"calendar:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # today_calendar cache 삭제
        now = await time_now()
        redis_key = f"today_calendar_list:{self.user.id}:{now.day}"
        await self.redis.delete(redis_key)

        return calendar

    async def delete(self, calendar_id: int) -> None:

        # 캘린더 조회
        calendar = self.db.query(Calendar).filter(Calendar.id == calendar_id, Calendar.User_id == self.user.id, Calendar.is_deleted == False).first()

        # 캘린더가 없을 경우 예외 처리
        if not calendar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4015,
            )

        # 캘린더 삭제
        calendar.is_deleted = True
        save_db(calendar, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"calendar:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # today_calendar cache 삭제
        now = await time_now()
        redis_key = f"today_calendar_list:{self.user.id}:{now.day}"
        await self.redis.delete(redis_key)


    async def list(self, year: int, month: int, day: int) -> list:
        import datetime

        # 잘못된 날짜 입력시 예외처리
        if month < 1 or month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4301,
            )
        if day < 0 or day > 31:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4301,
            )

        # day가 0일 경우 월간 캘린더 조회
        if day == 0:

            # redis에서 캐싱된 캘린더 조회
            redis_key = f"calendar:list:{self.user.id}:{year}:{month}"
            redis_data = await self.redis.get(redis_key)
            if redis_data:
                return json.loads(redis_data)

            # 캐싱된 캘린더가 없을 경우 db에서 조회
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

            # redis에서 캐싱된 캘린더 조회
            redis_key = f"calendar:list:{self.user.id}:{year}:{month}:{day}"
            redis_data = await self.redis.get(redis_key)
            if redis_data:
                return json.loads(redis_data)
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

        calenders_dict_list = []
        for calendar in calendars:
            calendar_dict = calendar.__dict__.copy()
            calendar_dict.pop('_sa_instance_state', None)
            calenders_dict_list.append(calendar_dict)

        # redis에 캐싱
        await self.redis.set(redis_key, json.dumps({"list": calenders_dict_list}, default=str, ensure_ascii=False), ex=1800)

        return {"list": calenders_dict_list}