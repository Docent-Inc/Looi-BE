from decimal import Decimal

import aiocron
import pytz
import redis
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy import func

from app.core.config import settings
from app.core.security import time_now
from app.db.database import get_SessionLocal, get_redis_client
from app.db.models import User, ApiRequestLog, MorningDiary, NightDiary, Calender, Memo, Report, Dashboard


def calculate_api_usage_cost(db, now):
    # GPT-3.5 Turbo 모델에 대한 로그를 가져옵니다.
    gpt3_logs = db.query(
        func.sum(ApiRequestLog.request_token),
        func.sum(ApiRequestLog.response_token)
    ).filter(
        func.date(ApiRequestLog.create_date) == now.date(),
        ApiRequestLog.model == "gpt-3.5-turbo-0613"
    ).first()

    # GPT-4 모델에 대한 로그를 가져옵니다.
    gpt4_logs = db.query(
        func.sum(ApiRequestLog.request_token),
        func.sum(ApiRequestLog.response_token)
    ).filter(
        func.date(ApiRequestLog.create_date) == now.date(),
        ApiRequestLog.model == "gpt-4-0613"
    ).first()

    # 각 모델의 토큰 가격을 설정합니다.
    prices = {
        "gpt-3.5-turbo-0613": (Decimal('0.0015'), Decimal('0.002')),
        "gpt-4-0613": (Decimal('0.03'), Decimal('0.06')),
    }

    # 비용을 계산하는 내부 함수입니다.
    def calculate_cost(logs, model):
        request_tokens, response_tokens = (Decimal(log) if log else 0 for log in logs)
        input_price, output_price = prices[model]
        input_cost = (request_tokens / 1000) * input_price
        output_cost = (response_tokens / 1000) * output_price
        return input_cost + output_cost

    # 각 모델에 대한 총 비용을 계산합니다.
    total_cost3 = calculate_cost(gpt3_logs, "gpt-3.5-turbo-0613")
    total_cost4 = calculate_cost(gpt4_logs, "gpt-4-0613")

    # 총 비용을 반환합니다.
    return float(total_cost3 + total_cost4)

async def slack_bot():
    client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
    SessionLocal = get_SessionLocal()
    db = SessionLocal()
    redis_client = get_redis_client()
    try:
        # 1. 오늘 가입한 유저 수
        # 2. 오늘 요청한 채팅 수
        # 3. 오늘 사용된 api 가격
        # 4. 오늘 생성된 아침 일기 수
        # 5. 오늘 생성된 저녁 일기 수
        # 6. 오늘 생성된 캘린더 수
        # 7. 오늘 생성된 메모 수
        # 8. 전체 유저 수
        # 9. 전체 요청 채팅 수
        # 10. 전체 사용된 api 가격
        # 11. 전체 생성된 아침 일기 수
        # 12. 전체 생성된 저녁 일기 수
        # 13. 전체 생성된 캘린더 수
        # 14. 전체 생성된 메모 수
        # 15. 전체 생성된 리포트 수

        now = await time_now()
        today_users = db.query(User).filter(
            func.date(User.create_date) == now.date(),
        ).all()
        today_users_count = len(today_users)
        text = f"오늘 가입한 유저 수: {today_users_count}\n"

        total_count_key = f"chat_count:total"
        total_count = redis_client.get(total_count_key) or 0
        text += f"오늘 요청한 채팅 수: {total_count}\n"

        total_cost = calculate_api_usage_cost(db, now)
        text += f"오늘 사용된 api 가격: ${total_cost:.2f}$\n"

        # 오늘 생성된 아침 일기 수
        morning_diary_count = db.query(MorningDiary).filter(
            func.date(MorningDiary.create_date) == now.date(),
        ).count()
        text += f"오늘 생성된 아침 일기 수: {morning_diary_count}\n"

        # 오늘 생성된 저녁 일기 수
        evening_diary_count = db.query(NightDiary).filter(
            func.date(NightDiary.create_date) == now.date(),
        ).count()
        text += f"오늘 생성된 저녁 일기 수: {evening_diary_count}\n"

        # 오늘 생성된 캘린더 수
        calender_count = db.query(Calender).filter(
            func.date(Calender.create_date) == now.date(),
        ).count()
        text += f"오늘 생성된 캘린더 수: {calender_count}\n"

        # 오늘 생성된 메모 수
        memo_count = db.query(Memo).filter(
            func.date(Memo.create_date) == now.date(),
        ).count()
        text += f"오늘 생성된 메모 수: {memo_count}\n\n"

        save = Dashboard(
            create_date=now,
            today_user=today_users_count,
            today_chat=total_count,
            today_cost=total_cost,
            today_morning_diary=morning_diary_count,
            today_night_diary=evening_diary_count,
            today_calender=calender_count,
            today_memo=memo_count,
        )
        db.add(save)
        db.commit()

        # 전체 유저 수
        total_users_count = db.query(User).count()
        text += f"전체 유저 수: {total_users_count}\n"

        # 전체 생성된 아침 일기 수
        total_morning_diary_count = db.query(MorningDiary).count()
        text += f"전체 생성된 아침 일기 수: {total_morning_diary_count}\n"

        # 전체 생성된 저녁 일기 수
        total_evening_diary_count = db.query(NightDiary).count()
        text += f"전체 생성된 저녁 일기 수: {total_evening_diary_count}\n"

        # 전체 생성된 캘린더 수
        total_calender_count = db.query(Calender).count()
        text += f"전체 생성된 캘린더 수: {total_calender_count}\n"

        # 전체 생성된 메모 수
        total_memo_count = db.query(Memo).count()
        text += f"전체 생성된 메모 수: {total_memo_count}\n"

        # 전체 생성된 리포트 수
        total_report_count = db.query(Report).count()
        text += f"전체 생성된 리포트 수: {total_report_count}\n"

        await client.chat_postMessage(
            channel=settings.SLACK_ID,
            text=text
        )
    except SlackApiError as e:
        print(f"Error posting message: {e}")
    finally:
        db.close()

cron_task = aiocron.crontab('59 23 * * *', func=slack_bot, tz=pytz.timezone('Asia/Seoul'))