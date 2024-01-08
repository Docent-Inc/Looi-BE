import aioredis
from fastapi import Depends
from slack_sdk.web.async_client import AsyncWebClient

from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_db
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import json
from app.core.security import time_now
from app.db.database import get_redis_client, save_db
from app.db.models import Report, MorningDiary, NightDiary, Calendar
from app.db.models import User
from app.core.aiRequset import GPTService
from app.service.abstract import AbstractReportService
from app.service.push import PushService


class ReportService(AbstractReportService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db), redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def read(self, report_id: int) -> dict:
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
            "period": await self.calculate_period(report.create_date)
        }

    async def calculate_period(self, start_date):
        start_of_week = start_date - timedelta(days=start_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return {
            "start_date": start_of_week.strftime("%Y년 %m월 %d일"),
            "end_date": end_of_week.strftime("%Y년 %m월 %d일")
        }

    async def list(self, page: int) -> list:

        # redis에 저장된 데이터를 가져옵니다.
        redis_key = f"report:list:{self.user.id}:{page}"
        redis_data = await self.redis.get(redis_key)
        if redis_data:
            return json.loads(redis_data)

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
            NightDiary.diary_name != "나만의 기록 친구 Looi와의 특별한 첫 만남",
        ).all()

        generated_total_count = len(morning_diaries) + len(night_diaries)

        start_number = report_count - offset
        titles = [f"{start_number - idx}번째 돌아보기" for idx in range(len(reports))]

        # 페이지네이션을 위한 로직
        paginated_titles = titles[offset:offset + limit]

        # 기간 계산 로직을 추가합니다.
        periods = [await self.calculate_period(report.create_date) for report in generated_reports]

        response = {
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

        # redis에 데이터를 저장합니다.
        await self.redis.set(redis_key, json.dumps(response, ensure_ascii=False), ex=1800)

        # 리포트 정보와 함께 제목과 기간을 포함하여 반환합니다.
        return response

    async def generate(self) -> dict:
        async def validate_report_structure(report_data):
            try:
                report_data = json.loads(report_data)
            except:
                return False
            required_keys = {
                "mental_state": str,
                "positives": dict,
                "negatives": dict,
                "extroverted_activities": list,
                "introverted_activities": list,
                "recommendations": list,
                "statistics": dict,
                "keywords": list,
            }
            for key, expected_type in required_keys.items():
                if key not in report_data or not isinstance(report_data[key], expected_type):
                    return False
                if key in ["positives", "negatives"]:
                    if "comment" not in report_data[key] or not isinstance(report_data[key]["comment"], str):
                        return False
                    if "main_keyword" not in report_data[key] or not isinstance(report_data[key]["main_keyword"], str):
                        return False

            statistics = report_data["statistics"]
            if not ("extrovert" in statistics and isinstance(statistics["extrovert"], int)):
                return False
            if not ("introvert" in statistics and isinstance(statistics["introvert"], int)):
                return False

            if not all(isinstance(keyword, str) for keyword in report_data["keywords"]):
                return False
            return True

        async def check_count(user: User) -> bool:
            today = await time_now()
            one_week_ago = today - timedelta(days=6)

            # 이번주에 생성된 리포트가 있는지 확인합니다.
            report = self.db.query(Report).filter(
                Report.User_id == user.id,
                Report.is_deleted == False,
                Report.create_date >= one_week_ago.date(),
            ).first()

            if report:
                return False

            # Process Morning Diary
            morning_diaries = self.db.query(MorningDiary).filter(
                MorningDiary.User_id == user.id,
                MorningDiary.create_date.between(one_week_ago.date(), today),
                MorningDiary.is_deleted == False
            ).count()

            # Process Night Diary
            night_diaries = self.db.query(NightDiary).filter(
                NightDiary.User_id == user.id,
                NightDiary.create_date.between(one_week_ago.date(), today),
                NightDiary.is_deleted == False,
                NightDiary.diary_name != "나만의 기록 친구 Look-i와의 특별한 첫 만남",
            ).count()

            total_count = morning_diaries + night_diaries

            if total_count < 5:
                return False

            return True

        async def generate_report(user: User) -> Report:
            text = f"nickname: {user.nickname}\n"
            today = await time_now()
            one_week_ago = today - timedelta(days=6)

            # Process Morning Diary
            morning_diaries = self.db.query(MorningDiary).filter(
                MorningDiary.User_id == user.id,
                MorningDiary.create_date.between(one_week_ago.date(), today),
                MorningDiary.is_deleted == False
            ).all()

            text += "Dreams of the last week:\n" + "\n".join(diary.content for diary in morning_diaries)
            text = text[:300]

            # Process Night Diary
            night_diaries = self.db.query(NightDiary).filter(
                NightDiary.User_id == user.id,
                NightDiary.create_date.between(one_week_ago.date(), today),
                NightDiary.is_deleted == False,
                NightDiary.diary_name != "나만의 기록 친구 Looi와의 특별한 첫 만남",
            ).all()

            text += "\nDiary for the last week:\n" + "\n".join(diary.content for diary in night_diaries)
            text = text[:1400]

            # Process Calendar
            calenders = self.db.query(Calendar).filter(
                Calendar.User_id == user.id,
                Calendar.start_time.between(one_week_ago.date(), today),
                Calendar.is_deleted == False
            ).all()

            text += "\nSchedule for the last week:\n" + "\n".join(
                f"{content.title}: {content.content}" for content in calenders)
            retries = 0
            is_success = False
            MAX_RETRIES = 3
            gpt_service = GPTService(user, self.db)
            while is_success == False and retries < MAX_RETRIES:
                report_data = await gpt_service.send_gpt_request(7, text)
                if not await validate_report_structure(report_data):
                    print(f"Invalid report structure for user {user.nickname}, retrying...{retries + 1}")
                    retries += 1
                else:
                    is_success = True

            if retries >= MAX_RETRIES:
                print(f"Failed to generate report for user {user.nickname}")
                client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
                await client.chat_postMessage(
                    channel="C064ZCNDVU1",
                    text=f"{user.nickname}님의 리포트 생성에 실패했습니다. 관리자에게 문의해주세요."
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=4600
                )

            data = json.loads(report_data)
            text = "다음 내용을 바탕으로 추상적인 이미지를 생성해주세요(no text).\n"
            text += data["mental_state"]
            image_url = await gpt_service.send_dalle_request(messages_prompt=text)

            mental_report = Report(
                User_id=user.id,
                content=json.dumps(data, ensure_ascii=False),
                create_date=today,
                image_url=image_url,
                is_deleted=False,
            )
            report = save_db(mental_report, self.db)
            return report

        lock_key = "generate_report_lock"
        if await self.redis.set(lock_key, "locked", ex=60, nx=True):
            try:
                users = self.db.query(User).filter(
                    User.is_deleted == False,
                ).all()
                total_count = 0
                generate_user_list = []
                push_service = PushService(db=self.db, user=self.user)
                for user in users:
                    print(f"processing {user.nickname}")
                    if await check_count(user):
                        total_count += 1
                        generate_user_list.append(user)
                print(f"total_count: {total_count}")
                for user in generate_user_list:
                    report = await generate_report(user)
                    print(f"{user.nickname} 유저 리포트 생성 완료")
                    if user.push_report == True:
                        await push_service.send(
                            title="Looi",
                            body=f"{user.nickname}님의 한 주 돌아보기 보고서를 만들었어요! 얼른 확인해 보세요~!",
                            image_url=report.image_url,
                            landing_url=f"/report/{report.id}",
                            token=user.push_token
                        )
                    print(f"progress: {generate_user_list.index(user) + 1}/{total_count}")
            finally:
                self.db.close()
                await self.redis.delete(lock_key)