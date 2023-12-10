import asyncio
from datetime import timedelta
import aiocron
import pytz
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import json

from app.core.security import time_now
from app.db.database import get_SessionLocal, get_redis_client, try_to_acquire_lock, release_lock, save_db
from app.db.models import Report, MorningDiary, NightDiary, Calender
from app.feature.aiRequset import send_gpt4_request
from app.db.models import User
from app.feature.generate import generate_image
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
            tasks = [generate_report(user, db) for user in users]
            await asyncio.gather(*tasks)
        finally:
            db.close()
            await release_lock(redis_client, lock_key)

# cron_task = aiocron.crontab('0 19 * * 0', func=generate, start=False, tz=pytz.timezone('Asia/Seoul'))
# cron_task.start()

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
def calculate_period(start_date):
    start_of_week = start_date - timedelta(days=start_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return {
        "start_date": start_of_week.strftime("%Y년 %m월 %d일"),
        "end_date": end_of_week.strftime("%Y년 %m월 %d일")
    }

async def generate_report(user: User, db: Session) -> str:
    text = f"nickname: {user.nickname}\n"
    today = await time_now()
    one_week_ago = today - timedelta(days=7)
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

    # if total_count < 5:
    #     return False

    # Process Calender
    calenders = db.query(Calender).filter(
        Calender.User_id == user.id,
        Calender.start_time.between(one_week_ago.date(), today),
        Calender.is_deleted == False
    ).all()

    text += "\nSchedule for the last week:\n" + "\n".join(f"{content.title}: {content.content}" for content in calenders)
    print(text)
    retries = 0
    is_success = False
    MAX_RETRIES = 3
    while is_success == False and retries < MAX_RETRIES:
        report_data = await send_gpt4_request(3, text, user, db)
        if not validate_report_structure(report_data):
            print(f"Invalid report structure for user {user.nickname}, retrying...{retries+1}")
            retries += 1
        else:
            is_success = True

    if retries >= MAX_RETRIES:
        return False
    data = json.loads(report_data)
    text = data["mental_state"]
    L = await generate_image(1, text, user, db)

    mental_report = Report(
        User_id=user.id,
        content=json.dumps(data, ensure_ascii=False),
        create_date=today,
        image_url=L[0],
        is_deleted=False,
    )
    save_db(mental_report, db)
    return mental_report.id

async def read_report(id: int, user: User, db: Session) -> dict:
    report = db.query(Report).filter(
        Report.User_id == user.id,
        Report.id == id,
        Report.is_deleted == False
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4020
        )

    if report.is_read == False:
        report.is_read = True
        db.commit()

    data = json.loads(report.content)
    period = calculate_period(report.create_date)

    return {
        "id": report.id,
        "content": data,
        "image_url": report.image_url,
        "create_date": report.create_date.strftime("%Y년 %m월 %d일"),
        "period": period
    }

async def list_report(page:int, user: User, db: Session) -> list:
    limit = 6
    offset = (page - 1) * limit
    reports = db.query(Report).filter(
        Report.User_id == user.id,
        Report.is_deleted == False
    ).order_by(Report.create_date.desc()).all()  # 주의: 오름차순으로 변경

    report_count = len(reports)  # 모든 리포트의 개수를 가져옴
    generated_reports = reports[offset:offset + limit]  # 현재 페이지에 해당하는 리포트

    # 현재 날짜와 시간을 구합니다.
    today = await time_now()

    # 현재 날짜가 속한 주의 월요일 날짜를 계산합니다.
    weekday = today.weekday()  # 월요일은 0, 일요일은 6
    monday = today - timedelta(days=weekday)  # 이번 주 월요일

    morning_diaries = db.query(MorningDiary).filter(
        MorningDiary.User_id == user.id,
        MorningDiary.create_date.between(monday.date(), today),
        MorningDiary.is_deleted == False
    ).all()

    night_diaries = db.query(NightDiary).filter(
        NightDiary.User_id == user.id,
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