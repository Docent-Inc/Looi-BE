import json
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, time_now
from app.db.database import get_db
from app.db.models import Report, MorningDiary, NightDiary
from app.schemas.response import User

async def calculate_period(start_date):
    start_of_week = start_date - timedelta(days=start_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return {
        "start_date": start_of_week.strftime("%Y년 %m월 %d일"),
        "end_date": end_of_week.strftime("%Y년 %m월 %d일")
    }

class ReportService:
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        self.user = user
        self.db = db

    async def create(self, user_id: int):
        pass

    async def read(self, report_id: int):
        report = self.db.query(Report).filter(
            Report.User_id == self.user.id,
            Report.id == report_id,
            Report.is_deleted == False
        ).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4020
            )

        if report.is_read == False:
            report.is_read = True
            self.db.commit()

        data = json.loads(report.content)

        return {
            "id": report.id,
            "content": data,
            "image_url": report.image_url,
            "create_date": report.create_date.strftime("%Y년 %m월 %d일"),
            "period": await calculate_period(report.create_date)
        }

    async def list(self, page: int):
        limit = 6
        offset = (page - 1) * limit
        reports = self.db.query(Report).filter(
            Report.User_id == self.user.id,
            Report.is_deleted == False
        ).order_by(Report.create_date.desc()).all()  # 주의: 오름차순으로 변경

        report_count = len(reports)  # 모든 리포트의 개수를 가져옴
        generated_reports = reports[offset:offset + limit]  # 현재 페이지에 해당하는 리포트

        # 현재 날짜와 시간을 구합니다.
        today = await time_now()

        # 현재 날짜가 속한 주의 월요일 날짜를 계산합니다.
        weekday = today.weekday()  # 월요일은 0, 일요일은 6
        monday = today - timedelta(days=weekday)  # 이번 주 월요일

        morning_diaries = self.db.query(MorningDiary).filter(
            MorningDiary.User_id == self.user.id,
            MorningDiary.create_date.between(monday.date(), today),
            MorningDiary.is_deleted == False
        ).all()

        night_diaries = self.db.query(NightDiary).filter(
            NightDiary.User_id == self.user.id,
            NightDiary.create_date.between(monday.date(), today),
            NightDiary.is_deleted == False,
            NightDiary.diary_name != "나만의 기록 친구 Look-i와의 특별한 첫 만남",
        ).all()

        generated_total_count = len(morning_diaries) + len(night_diaries)

        start_number = report_count - offset
        titles = [f"{start_number - idx}번째 돌아보기" for idx in range(len(reports))]

        # 페이지네이션을 위한 로직
        paginated_titles = titles[offset:offset + limit]

        # 기간 계산 로직을 추가합니다.
        periods = [calculate_period(report.create_date) for report in generated_reports]

        # 리포트 정보와 함께 제목과 기간을 포함하여 반환합니다.
        return {
            "generated_total_count": generated_total_count,
            "list_count": report_count,
            "reports": [
                {
                    "id": report.id,
                    "title": title,
                    "period": period,
                    "main_keyword": json.loads(report.content)["keywords"],
                    "image_url": report.image_url,
                    "create_date": report.create_date.strftime("%Y년 %m월 %d일"),
                    "is_read": report.is_read
                } for title, period, report in zip(paginated_titles, periods, generated_reports)
            ]
        }