from fastapi import Depends
from app.core.security import get_current_user
from app.db.database import get_db
from app.schemas.response import User
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import json
from app.core.security import time_now
from app.db.database import get_SessionLocal, get_redis_client, try_to_acquire_lock, release_lock, save_db
from app.db.models import Report, MorningDiary, NightDiary, Calendar
from app.db.models import User
from app.feature.aiRequset import GPTService

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
async def generate():
    redis_client = await get_redis_client()
    lock_key = "generate_report_lock"
    if await try_to_acquire_lock(redis_client, lock_key):
        SessionLocal = get_SessionLocal()
        db = SessionLocal()
        try:
            users = db.query(User).filter(
                User.is_deleted == False,
            ).all()
            for user in users:
                await generate_report(user, db)
        finally:
            db.close()
            await release_lock(redis_client, lock_key)

def validate_report_structure(report_data):
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

async def generate_report(user: User, db: Session) -> str:
    text = f"nickname: {user.nickname}\n"
    today = await time_now()
    one_week_ago = today - timedelta(days=6)
    total_count = 0

    # 6일 이내의 데이터가 있으면 에러 반환
    report = db.query(Report).filter(
        Report.User_id == user.id,
        Report.create_date <= today,
        Report.create_date >= one_week_ago.date(),
        Report.is_deleted == False
    ).first()

    if report:
        return False

    # Process Morning Diary
    morning_diaries = db.query(MorningDiary).filter(
        MorningDiary.User_id == user.id,
        MorningDiary.create_date.between(one_week_ago.date(), today),
        MorningDiary.is_deleted == False
    ).all()

    text += "Dreams of the last week:\n" + "\n".join(diary.content for diary in morning_diaries)
    total_count += len(morning_diaries)

    # Process Night Diary
    night_diaries = db.query(NightDiary).filter(
        NightDiary.User_id == user.id,
        NightDiary.create_date.between(one_week_ago.date(), today),
        NightDiary.is_deleted == False,
        NightDiary.content != "오늘은 인상깊은 날이다. 기록 친구 Look-i와 만나게 되었다. 앞으로 기록 열심히 해야지~!"
    ).all()

    text += "\nDiary for the last week:\n" + "\n".join(diary.content for diary in night_diaries)
    total_count += len(night_diaries)

    if total_count < 5:
        return False

    # Process Calendar
    calenders = db.query(Calendar).filter(
        Calendar.User_id == user.id,
        Calendar.start_time.between(one_week_ago.date(), today),
        Calendar.is_deleted == False
    ).all()

    text += "\nSchedule for the last week:\n" + "\n".join(f"{content.title}: {content.content}" for content in calenders)
    retries = 0
    is_success = False
    MAX_RETRIES = 3
    while is_success == False and retries < MAX_RETRIES:
        gpt_service = GPTService(user, db)
        report_data = await gpt_service.send_gpt_request(7, text)
        if not validate_report_structure(report_data):
            print(f"Invalid report structure for user {user.nickname}, retrying...{retries+1}")
            retries += 1
        else:
            is_success = True

    if retries >= MAX_RETRIES:
        return False

    data = json.loads(report_data)
    text = "다음 내용을 바탕으로 추상적인 이미지를 생성해주세요"
    text += data["mental_state"]
    image_url = await gpt_service.send_dalle_request(messages_prompt=text, background=False)

    mental_report = Report(
        User_id=user.id,
        content=json.dumps(data, ensure_ascii=False),
        create_date=today,
        image_url=image_url,
        is_deleted=False,
    )
    save_db(mental_report, db)
    return mental_report.id