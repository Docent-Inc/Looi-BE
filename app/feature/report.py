import time
from datetime import timedelta

import aiocron
import pytz
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
import json

from app.core.security import time_now
from app.db.database import get_SessionLocal
from app.db.models import Report, MorningDiary, NightDiary, Calender
from app.feature.aiRequset import send_gpt4_request
from app.db.models import User

async def generate():
    SessionLocal = get_SessionLocal()
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            print(f"Generating report for {user.nickname}")
            is_success = await generate_report(user, db)
            if is_success:
                print(f"Report generated for {user.nickname}")
            else:
                print(f"Report error for {user.nickname}")
    finally:
        db.close()

cron_task = aiocron.crontab('0 0 * * *', func=generate, tz=pytz.timezone('Asia/Seoul'))

def validate_report_structure(report_data):
    required_keys = {
        "mental_state": str,
        "positives": dict,
        "negatives": dict,
        "extroverted_activities": list,
        "introverted_activities": list,
        "recommendations": list,
        "statistics": list
    }
    for key, expected_type in required_keys.items():
        if key not in report_data or not isinstance(report_data[key], expected_type):
            return False
        if key in ["positives", "negatives"]:
            if "comment" not in report_data[key] or "main_keyword" not in report_data[key]:
                return False
    if not (isinstance(report_data["statistics"][0], dict) and isinstance(report_data["statistics"][1], list)):
        return False
    return True

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
        NightDiary.is_deleted == False
    ).all()

    text += "\nDiary for the last week:\n" + "\n".join(diary.content for diary in night_diaries)
    total_count += len(night_diaries)

    if total_count < 5:
        return False

    # Process Calender
    calenders = db.query(Calender).filter(
        Calender.User_id == user.id,
        Calender.start_time.between(one_week_ago.date(), today),
        Calender.is_deleted == False
    ).all()

    text += "\nSchedule for the last week:\n" + "\n".join(content.title for content in calenders)

    report_data = await send_gpt4_request(3, text, user, db)
    parsed_report_data = json.loads(report_data)
    if not validate_report_structure(parsed_report_data):
        print(f"Invalid report structure for user {user.nickname}")
        return False

    mental_report = Report(
        User_id=user.id,
        content=json.dumps(report, ensure_ascii=False),
        create_date=today,
        is_deleted=False,
    )
    db.add(mental_report)
    db.commit()
    return True

async def read_report(id: int, user: User, db: Session) -> str:
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

    return json.loads(report.content)

async def list_report(page:int, user: User, db: Session) -> list:
    limit = 6
    offset = (page - 1) * limit
    reports = db.query(Report).filter(
        Report.User_id == user.id,
        Report.is_deleted == False
    ).order_by(Report.create_date.desc()).limit(limit).offset(offset).all()

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
        NightDiary.is_deleted == False
    ).all()

    total_count = len(morning_diaries) + len(night_diaries)

    return {"total_count": total_count}, [
            {
                "id": report.id,
                "main_keyword": json.loads(report.content)["statistics"][1],
                "image_url": report.image_url,
                "create_date": report.create_date,
                "is_read": report.is_read
            } for report in reports
        ]


