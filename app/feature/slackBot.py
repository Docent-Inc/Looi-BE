from decimal import Decimal
import aiocron
import pytz
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy import func

from app.core.config import settings
from app.core.security import time_now
from app.db.database import get_SessionLocal, get_redis_client, try_to_acquire_lock, release_lock
from app.db.models import User, ApiRequestLog, MorningDiary, NightDiary, Calender, Memo, Report, Dashboard, \
    TextClassification


def calculate_api_usage_cost(db, now):
    # GPT-3.5 Turbo 모델에 대한 로그를 가져옵니다.
    gpt3_logs = db.query(
        func.sum(ApiRequestLog.request_token),
        func.sum(ApiRequestLog.response_token)
    ).filter(
        func.date(ApiRequestLog.create_date) == now.date(),
        ApiRequestLog.model == "gpt-3.5-turbo-1106"
    ).first()

    # GPT-4 모델에 대한 로그를 가져옵니다.
    gpt4_turbo_logs = db.query(
        func.sum(ApiRequestLog.request_token),
        func.sum(ApiRequestLog.response_token)
    ).filter(
        func.date(ApiRequestLog.create_date) == now.date(),
        ApiRequestLog.model == "gpt-4-1106-preview"
    ).first()

    gpt4_logs = db.query(
        func.sum(ApiRequestLog.request_token),
        func.sum(ApiRequestLog.response_token)
    ).filter(
        func.date(ApiRequestLog.create_date) == now.date(),
        ApiRequestLog.model == "gpt-4-0613"
    ).first()


    # DaLLE-2 모델에 대한 로그를 가져옵니다.
    dalle_logs = db.query(
        func.count(ApiRequestLog.id)
    ).filter(
        func.date(ApiRequestLog.create_date) == now.date(),
        ApiRequestLog.model == "DaLLE-3"
    ).scalar()  # .count() 대신 .scalar()를 사용하여 바로 값을 가져올 수 있습니다.

    # 각 모델의 토큰 가격을 설정합니다.
    prices = {
        "gpt-3.5-turbo-1106": (Decimal('0.001'), Decimal('0.002')),
        "gpt-4-1106-preview": (Decimal('0.01'), Decimal('0.03')),
        "gpt-4-0613": (Decimal('0.03'), Decimal('0.06')),
        "DaLLE-3": Decimal('0.040')  # DaLLE-2 모델의 가격
    }

    # 비용을 계산하는 내부 함수입니다.
    def calculate_cost(logs, model):
        if model in ["gpt-3.5-turbo-1106", "gpt-4-1106-preview", "gpt-4-0613"]:
            request_tokens, response_tokens = (Decimal(log) if log else 0 for log in logs)
            input_price, output_price = prices[model]
            input_cost = (request_tokens / Decimal(1000)) * input_price
            output_cost = (response_tokens / Decimal(1000)) * output_price
            return input_cost + output_cost
        elif model == "DaLLE-3":
            requests = Decimal(logs if logs else 0)
            price_per_request = prices[model]
            return requests * price_per_request

    # 각 모델에 대한 총 비용을 계산합니다.
    total_cost3 = calculate_cost(gpt3_logs, "gpt-3.5-turbo-1106")
    total_cost4_turbo = calculate_cost(gpt4_turbo_logs, "gpt-4-1106-preview")
    total_cost4 = calculate_cost(gpt4_logs, "gpt-4-0613")
    total_cost_dalle = calculate_cost(dalle_logs, "DaLLE-3")

    # 총 비용을 반환합니다.
    return float(total_cost3 + total_cost4 + total_cost_dalle + total_cost4_turbo)

async def slack_bot():
    client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
    SessionLocal = get_SessionLocal()
    db = SessionLocal()
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

        total_count = db.query(TextClassification).filter(
            func.date(TextClassification.create_date) == now.date(),
        ).count()

        total_cost = calculate_api_usage_cost(db, now)

        # 오늘 채팅 요청을 한번이라도 한 사람 수
        today_chat_users = db.query(TextClassification).filter(
            func.date(TextClassification.create_date) == now.date(),
        ).group_by(TextClassification.User_id).all()
        today_chat_users_count = len(today_chat_users)

        mean_request = total_count / today_chat_users_count

        # 오늘 생성된 아침 일기 수
        morning_diary_count = db.query(MorningDiary).filter(
            func.date(MorningDiary.create_date) == now.date(),
        ).count()

        # 오늘 생성된 저녁 일기 수
        evening_diary_count = db.query(NightDiary).filter(
            func.date(NightDiary.create_date) == now.date(),
        ).count()

        # 오늘 생성된 캘린더 수
        calender_count = db.query(Calender).filter(
            func.date(Calender.create_date) == now.date(),
        ).count()

        # 오늘 생성된 메모 수
        memo_count = db.query(Memo).filter(
            func.date(Memo.create_date) == now.date(),
        ).count()
        dashboards = db.query(Dashboard).filter(
            func.date(Dashboard.create_date) == now.date(),
        ).first()
        if dashboards:
            dashboards.today_user = today_users_count
            dashboards.today_chat = total_count
            dashboards.today_cost = total_cost
            dashboards.today_morning_diary = morning_diary_count
            dashboards.today_night_diary = evening_diary_count
            dashboards.today_calender = calender_count
            dashboards.today_memo = memo_count
            dashboards.today_chat_user = today_chat_users_count
            dashboards.today_chat_mean_request = mean_request
            db.commit()
            db.refresh(dashboards)
        else:
            save = Dashboard(
                create_date=now,
                today_user=today_users_count,
                today_chat=total_count,
                today_cost=total_cost,
                today_morning_diary=morning_diary_count,
                today_night_diary=evening_diary_count,
                today_calender=calender_count,
                today_memo=memo_count,
                today_chat_user=today_chat_users_count,
                today_chat_mean_request=mean_request,
            )
            db.add(save)
            db.commit()
            db.refresh(save)

        # 전체 유저 수
        total_users_count = db.query(User).count()

        # 전체 생성된 아침 일기 수
        total_morning_diary_count = db.query(MorningDiary).count()

        # 전체 생성된 저녁 일기 수
        total_evening_diary_count = db.query(NightDiary).count()

        # 전체 생성된 캘린더 수
        total_calender_count = db.query(Calender).count()

        # 전체 생성된 메모 수
        total_memo_count = db.query(Memo).count()

        # 전체 생성된 리포트 수
        total_report_count = db.query(Report).count()

        # 전체 생성된 채팅 수
        total_chat_count = db.query(TextClassification).count()

        # 전체 게시물 공유 조회수
        MorningDiary_share_count_result = db.query(func.sum(MorningDiary.share_count)).scalar()
        NightDiary_share_count_result = db.query(func.sum(NightDiary.share_count)).scalar()

        total_share_count = MorningDiary_share_count_result + NightDiary_share_count_result

        current_date = now.strftime("%Y-%m-%d")

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{current_date} 오늘의 요약:*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*오늘 가입한 유저 수:* {today_users_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*오늘 요청한 채팅 수:* {total_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*오늘 사용된 API 비용:* ${total_cost:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*오늘 생성된 아침 일기 수:* {morning_diary_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*오늘 생성된 저녁 일기 수:* {evening_diary_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*오늘 생성된 캘린더 수:* {calender_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*오늘 생성된 메모 수:* {memo_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*오늘 평균 채팅 요청 수:* {mean_request:.2f}"
                    },
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*총계:*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*전체 유저 수:* {total_users_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*전체 생성된 아침 일기 수:* {total_morning_diary_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*전체 생성된 저녁 일기 수:* {total_evening_diary_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*전체 생성된 캘린더 수:* {total_calender_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*전체 생성된 메모 수:* {total_memo_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*전체 생성된 리포트 수:* {total_report_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*전체 생성된 채팅 수:* {total_chat_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*전체 공유 게시물 조회 수:* {total_share_count}"
                    },
                ]
            }
        ]
        await client.chat_postMessage(
            channel=settings.SLACK_ID,
            blocks=blocks
        )
    except SlackApiError as e:
        print(f"Error posting message: {e}")
    finally:
        db.close()

async def scheduled_task():
    redis_client = await get_redis_client()
    lock_key = "slakc_bot_lock"
    if await try_to_acquire_lock(redis_client, lock_key):
        try:
            await slack_bot()
        finally:
            await release_lock(redis_client, lock_key)