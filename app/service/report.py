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
from app.db.models import Report, MorningDiary, NightDiary, Calendar, PushQuestion
from app.db.models import User
from app.core.aiRequset import GPTService
from app.service.abstract import AbstractReportService
from app.service.push import PushService


async def calculate_period(start_date):
    start_of_week = start_date - timedelta(days=start_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return {
        "start_date": start_of_week.strftime("%Y년 %m월 %d일"),
        "end_date": end_of_week.strftime("%Y년 %m월 %d일")
    }


async def validate_report_structure(report_data):
    try:
        report_data = json.loads(report_data)
    except:
        return False
    required_keys = {
        # "mental_state": str,
        "positives": dict,
        "negatives": dict,
        "recommendations": list,
        "personal_questions": list,
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
        if key in ["recommendations", "personal_questions"]:
            if not all(isinstance(item, str) for item in report_data[key]):
                return False

    if not all(isinstance(keyword, str) for keyword in report_data["keywords"]):
        return False
    return True


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

        redis_key = f"report:list:{self.user.id}:*"
        await self.redis.delete(redis_key)

        return {
            "id": report.id,
            "content": data,
            "image_url": report.image_url,
            "create_date": report.create_date.strftime("%Y년 %m월 %d일"),
        }

    async def list(self, page: int) -> list:

        # redis에 저장된 데이터를 가져옵니다.
        redis_key = f"report:list:{self.user.id}:{page}"
        redis_data = await self.redis.get(redis_key)
        if redis_data:
            return json.loads(redis_data)

        limit = 6
        offset = (page - 1) * limit

        last_date, reports, diary_list = await self.check_count(self.user)

        generated_reports = reports[offset:offset + limit]

        # 각 페이지에 대한 올바른 시작 번호 계산
        start_number = len(reports) - offset

        # 현재 페이지에 해당하는 리포트에 대한 제목을 생성합니다.
        titles = [f"{start_number - idx}번째 마음 상태" for idx in range(len(generated_reports))]

        # # 기간 계산 로직을 추가합니다.
        # periods = [await self.calculate_period(report.create_date) for report in generated_reports]

        response = {
            "generated_total_count": len(diary_list),
            "list_count": len(reports),
            "reports": [
                {
                    "id": report.id,
                    "title": title,
                    "main_keyword": json.loads(report.content)["keywords"],
                    "image_url": report.image_url,
                    "create_date": report.create_date.strftime("%Y년 %m월 %d일"),
                    "is_read": report.is_read
                } for title, report in zip(titles, generated_reports)
            ]
        }

        # redis에 데이터를 저장합니다.
        await self.redis.set(redis_key, json.dumps(response, ensure_ascii=False), ex=1800)

        # 리포트 정보와 함께 제목과 기간을 포함하여 반환합니다.
        return response

    async def check_count(self, user: User) -> bool:
        # 모든 리포트를 가져옵니다 (내림차순 정렬).
        reports = self.db.query(Report).filter(
            Report.User_id == self.user.id,
            Report.is_deleted == False
        ).order_by(Report.create_date.desc()).all()
        #TODO: 페이징 기능 필요

        # 현재 날짜와 시간을 구합니다.
        today = await time_now()

        # 마지막 보고서 생성일 다음날 부터 오늘까지의 일기를 가져옵니다.
        last_report = reports[0]
        last_date = last_report.create_date + timedelta(days=1)

        night_diaries = self.db.query(NightDiary).filter(
            NightDiary.User_id == user.id,
            NightDiary.create_date.between(last_date.date(), today),
            NightDiary.is_deleted == False,
            NightDiary.diary_name != "나만의 기록 친구 Looi와의 특별한 첫 만남",
        ).all()

        diary_list = []
        for diary in night_diaries:
            if len(diary.content) > 50:
                diary_list.append(diary)

        return last_date, reports, diary_list

    async def generate(self) -> dict:
        text = f"nickname: {self.user.nickname}\n"
        today = await time_now()

        last_date, reports, diary_list = await self.check_count(self.user)
        if len(diary_list) < 3:
            return False

        text += "\nDiary for the last week:\n" + "\n".join(diary.content for diary in diary_list)
        text = text[:1400]

        # Process Calendar
        calenders = self.db.query(Calendar).filter(
            Calendar.User_id == self.user.id,
            Calendar.start_time.between(last_date.date(), today),
            Calendar.is_deleted == False
        ).all()

        text += "\nSchedule for the last week:\n" + "\n".join(
            f"{content.title}: {content.content}" for content in calenders)

        retries = 0
        is_success = False
        MAX_RETRIES = 3
        gpt_service = GPTService(self.user, self.db)
        while is_success == False and retries < MAX_RETRIES:
            report_data = await gpt_service.send_gpt_request(7, text)
            if not await validate_report_structure(report_data):
                print(f"Invalid report structure for user {self.user.nickname}, retrying...{retries + 1}")
                retries += 1
            else:
                is_success = True

        if retries >= MAX_RETRIES:
            print(f"Failed to generate report for user {self.user.nickname}")
            client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
            await client.chat_postMessage(
                channel="C064ZCNDVU1",
                text=f"{self.user.nickname}님의 리포트 생성에 실패했습니다. 관리자에게 문의해주세요."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=4600
            )

        data = json.loads(report_data)
        text = "다음 내용을 바탕으로 이미지를 생성해주세요(no text, digital art, illustration).\n"
        text += data["positives"]
        image_url = await gpt_service.send_dalle_request(messages_prompt=text)

        mental_report = Report(
            User_id=self.user.id,
            content=json.dumps(data, ensure_ascii=False),
            create_date=today,
            image_url=image_url,
            is_deleted=False,
        )
        report = save_db(mental_report, self.db)



        push_service = PushService(db=self.db, user=self.user)
        await push_service.send(
            title="Looi",
            body=f"{self.user.nickname}님의 기록을 토대로 마음 상태 보고서를 만들었어요 📜",
            device=f"{self.user.device}",
            image_url=report.image_url,
            landing_url=f"/report/{report.id}",
            token=self.user.push_token
        )

        now = await time_now()
        for push_question in data["personal_questions"]:
            push_question = PushQuestion(
                User_id=self.user.id,
                question_type="report",
                calendar_content="",
                is_pushed=False,
                question=push_question,
                create_date=now,
            )
            save_db(push_question, self.db)


        redis_key = f"report:list:{self.user.id}:*"
        await self.redis.delete(redis_key)

        return report