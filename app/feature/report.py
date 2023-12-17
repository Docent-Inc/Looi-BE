import asyncio
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import json

from app.core.security import time_now
from app.db.database import get_SessionLocal, get_redis_client, try_to_acquire_lock, release_lock, save_db
from app.db.models import Report, MorningDiary, NightDiary, Calendar
from app.db.models import User
from app.feature.aiRequset import GPTService
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
                print(user.nickname)
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

    if total_count < 2:
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
    print(text)
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
    text = data["mental_state"]
    image_url = await gpt_service.send_dalle_request(text)

    mental_report = Report(
        User_id=user.id,
        content=json.dumps(data, ensure_ascii=False),
        create_date=today,
        image_url=image_url,
        is_deleted=False,
    )
    save_db(mental_report, db)
    return mental_report.id