import json
import warnings
from datetime import timedelta, datetime
from decimal import Decimal

import aioredis
from fastapi import Depends
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy import inspect, func, distinct, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user_is_admin, time_now
from app.db.database import get_db, get_redis_client, save_db
from app.db.models import User, Dashboard, TextClassification, ApiRequestLog, MorningDiary, NightDiary, Calendar, Memo, \
    Report, ErrorLog
from app.service.abstract import AbstractAdminService

warnings.filterwarnings("ignore", category=UserWarning, module="slack_sdk")
class AdminService(AbstractAdminService):
    def __init__(self, user: User = Depends(get_current_user_is_admin), db: Session = Depends(get_db),
                 redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def user_list(self) -> list:
        users = self.db.query(User).all()
        user_list = []

        for user in users:
            user_dict = {c.key: getattr(user, c.key) for c in inspect(user).mapper.column_attrs}
            user_dict.pop("hashed_password", None)
            user_list.append(user_dict)

        return user_list

    async def dashboard(self) -> list:
        dashboard = self.db.query(Dashboard).all()
        return dashboard

    async def user_dream_data(self) -> list:
        results = self.db.execute(
            select(
                MorningDiary.User_id,
                User.mbti,
                MorningDiary.content,
                MorningDiary.resolution,
                MorningDiary.main_keyword,
                User.nickname
            ).join(User, MorningDiary.User_id == User.id)
        ).fetchall()

        data = []

        for user_id, mbti, content, resolution, main_keyword, nickname in results:
            keyword_list = []
            try:
                for keyword in json.loads(main_keyword):
                    keyword_list.append(keyword)
                dream_info = {
                    "Text": f"nickname: {nickname}, mbti: {mbti}, dream: {content}",
                    "Completion": {"resolution": resolution, "main_keywords": keyword_list}
                }
                dream_info["Completion"] = json.dumps(dream_info["Completion"], ensure_ascii=False)
                data.append(dream_info)
            except:
                pass

        print(len(data))
        return data

    async def user_diary_data(self) -> list:
        results = self.db.execute(
            select(
                NightDiary.User_id,
                NightDiary.content,
                NightDiary.resolution,
                NightDiary.main_keyword,
                User.nickname,
            ).join(User, NightDiary.User_id == User.id)
        ).fetchall()

        data = []

        for user_id, content, resolution, main_keyword, nickname in results:
            keyword_list = []
            try:
                if "오늘은 인상깊은 날이다." in content:
                    continue
                for keyword in json.loads(main_keyword):
                    keyword_list.append(keyword)
                dream_info = {
                    "Text": f"nickname: {nickname}, diary: {content}",
                    "Completion": {"reply": resolution, "main_keywords": keyword_list}
                }
                dream_info["Completion"] = json.dumps(dream_info["Completion"], ensure_ascii=False)
                data.append(dream_info)
            except:
                pass

        print(len(data))
        return data
    async def slack_bot(self) -> dict:
        async def calculate_api_usage_cost():
            now = await time_now()
            # GPT-3.5 Turbo 모델에 대한 로그를 가져옵니다.
            gpt3_logs = self.db.query(
                func.sum(ApiRequestLog.request_token),
                func.sum(ApiRequestLog.response_token)
            ).filter(
                func.date(ApiRequestLog.create_date) == now.date(),
                ApiRequestLog.model == "gpt-3.5-turbo-1106"
            ).first()

            # GPT-4 모델에 대한 로그를 가져옵니다.
            gpt4_turbo_logs = self.db.query(
                func.sum(ApiRequestLog.request_token),
                func.sum(ApiRequestLog.response_token)
            ).filter(
                func.date(ApiRequestLog.create_date) == now.date(),
                ApiRequestLog.model == "gpt-4-1106-preview"
            ).first()

            gpt3_turbo_logs = self.db.query(
                func.sum(ApiRequestLog.request_token),
                func.sum(ApiRequestLog.response_token)
            ).filter(
                func.date(ApiRequestLog.create_date) == now.date(),
                ApiRequestLog.model == "gpt-3.5-turbo"
            ).first()

            # DaLLE-2 모델에 대한 로그를 가져옵니다.
            dalle_logs = self.db.query(
                func.count(ApiRequestLog.id)
            ).filter(
                func.date(ApiRequestLog.create_date) == now.date(),
                ApiRequestLog.model == "DaLLE-3"
            ).scalar()  # .count() 대신 .scalar()를 사용하여 바로 값을 가져올 수 있습니다.

            # 각 모델의 토큰 가격을 설정합니다.
            prices = {
                "gpt-3.5-turbo": (Decimal('0.0015'), Decimal('0.002')),
                "gpt-3.5-turbo-1106": (Decimal('0.001'), Decimal('0.002')),
                "gpt-4-1106-preview": (Decimal('0.01'), Decimal('0.03')),
                "DaLLE-3": Decimal('0.040')
            }

            def calculate_cost(logs, model):
                if model in ["gpt-3.5-turbo-1106", "gpt-4-1106-preview", "gpt-3.5-turbo"]:
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
            total_cost3_turbo = calculate_cost(gpt3_turbo_logs, "gpt-3.5-turbo")
            total_cost_dalle = calculate_cost(dalle_logs, "DaLLE-3")

            # 총 비용을 반환합니다.
            return float(total_cost3 + total_cost3_turbo + total_cost_dalle + total_cost4_turbo)

        async def slack_bot():
            client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
            try:
                now = await time_now()

                # 오늘 생성된 유저 수
                today_users = self.db.query(User).filter(
                    func.date(User.create_date) == now.date(),
                ).all()
                today_users_count = len(today_users)

                # 오늘 사용된 api 비용
                total_cost = await calculate_api_usage_cost()

                # 오늘 생성된 아침 일기 수
                morning_diary_count = self.db.query(MorningDiary).filter(
                    func.date(MorningDiary.create_date) == now.date(),
                ).count()

                # 오늘 생성된 저녁 일기 수
                evening_diary_count = self.db.query(NightDiary).filter(
                    func.date(NightDiary.create_date) == now.date(),
                    NightDiary.diary_name != "나만의 기록 친구 Looi와의 특별한 첫 만남",
                ).count()

                # 오늘 생성된 캘린더 수
                calender_count = self.db.query(Calendar).filter(
                    func.date(Calendar.create_date) == now.date(),
                ).count()

                # 오늘 생성된 메모 수
                memo_count = self.db.query(Memo).filter(
                    func.date(Memo.create_date) == now.date(),
                ).count()

                # 오늘 생성된 기록 수
                total_count = morning_diary_count + evening_diary_count + calender_count + memo_count



                dashboards = self.db.query(Dashboard).filter(
                    func.date(Dashboard.create_date) == now.date(),
                ).first()

                dau_count = self.db.query(distinct(MorningDiary.User_id)).filter(
                    func.date(MorningDiary.create_date) == now.date(),
                ).union(
                    self.db.query(distinct(NightDiary.User_id)).filter(
                        func.date(NightDiary.create_date) == now.date()
                    ),
                    self.db.query(distinct(Memo.User_id)).filter(
                        func.date(Memo.create_date) == now.date()
                    ),
                    self.db.query(distinct(Calendar.User_id)).filter(
                        func.date(Calendar.create_date) == now.date()
                    )
                ).count()

                # 평균 기록 수
                mean_request = total_count / dau_count

                last_week = now.date() - timedelta(days=7)
                wau_count = self.db.query(distinct(MorningDiary.User_id)).filter(
                    func.date(MorningDiary.create_date) >= last_week,
                    func.date(MorningDiary.create_date) <= now.date()
                ).union(
                    self.db.query(distinct(NightDiary.User_id)).filter(
                        func.date(NightDiary.create_date) >= last_week,
                        func.date(NightDiary.create_date) <= now.date()
                    ),
                    self.db.query(distinct(Memo.User_id)).filter(
                        func.date(Memo.create_date) >= last_week,
                        func.date(Memo.create_date) <= now.date()
                    ),
                    self.db.query(distinct(Calendar.User_id)).filter(
                        func.date(Calendar.create_date) >= last_week,
                        func.date(Calendar.create_date) <= now.date()
                    )
                ).count()

                last_month = now.date() - timedelta(days=30)
                mau_count = self.db.query(distinct(MorningDiary.User_id)).filter(
                    func.date(MorningDiary.create_date) >= last_month,
                    func.date(MorningDiary.create_date) <= now.date()
                ).union(
                    self.db.query(distinct(NightDiary.User_id)).filter(
                        func.date(NightDiary.create_date) >= last_month,
                        func.date(NightDiary.create_date) <= now.date()
                    ),
                    self.db.query(distinct(Memo.User_id)).filter(
                        func.date(Memo.create_date) >= last_month,
                        func.date(Memo.create_date) <= now.date()
                    ),
                    self.db.query(distinct(Calendar.User_id)).filter(
                        func.date(Calendar.create_date) >= last_month,
                        func.date(Calendar.create_date) <= now.date()
                    )
                ).count()

                # DAU / MAU
                dau_to_mau = (dau_count / mau_count) * 100

                # DAU / WAU
                dau_to_wau = (dau_count / wau_count) * 100

                # dau 증감율 계산
                yesterday_dau_count = self.db.query(Dashboard).filter(
                    func.date(Dashboard.create_date) == (now.date() - timedelta(days=1))
                ).first()
                yesterday_dau_count = yesterday_dau_count.dau if yesterday_dau_count else 0
                dau_growth_rate = ((dau_count - yesterday_dau_count) / max(yesterday_dau_count, 1)) * 100

                # 전체 유저 수
                total_users_count = self.db.query(User).count()

                # 전체 생성된 아침 일기 수
                total_morning_diary_count = self.db.query(MorningDiary).count()

                # 전체 생성된 저녁 일기 수
                total_evening_diary_count = self.db.query(NightDiary).count()
                total_evening_diary_count -= total_users_count

                # 전체 생성된 캘린더 수
                total_calendar_count = self.db.query(Calendar).count()

                # 전체 생성된 메모 수
                total_memo_count = self.db.query(Memo).count()

                # 전체 생성된 리포트 수
                total_report_count = self.db.query(Report).filter().count()

                # 전체 게시물 공유 조회수
                MorningDiary_share_count_result = self.db.query(func.sum(MorningDiary.share_count)).scalar()
                NightDiary_share_count_result = self.db.query(func.sum(NightDiary.share_count)).scalar()

                # 전체 공유 조회수
                total_share_count = MorningDiary_share_count_result + NightDiary_share_count_result

                # 오늘 날짜
                current_date = now.strftime("%Y-%m-%d")

                # 탈퇴한 유저 수
                withdraw_users_count = self.db.query(User).filter(
                    User.is_deleted == True
                ).count()

                # 오늘 에러가 발생한 수
                today_error_count = self.db.query(ErrorLog).filter(
                    func.date(ErrorLog.create_date) == now.date(),
                ).count()

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
                                "text": f"*오늘 기록 수:* {total_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*오늘 사용된 API 비용:* ${total_cost:.2f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*오늘 생성된 꿈 수:* {morning_diary_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*오늘 생성 일기 수:* {evening_diary_count}"
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
                                "text": f"*오늘 평균 기록 수:* {mean_request:.2f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*오늘 오류 발생 횟수:* {today_error_count}"
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
                                "text": f"*전체 생성된 꿈 수:* {total_morning_diary_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*전체 생성된 일기 수:* {total_evening_diary_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*전체 생성된 캘린더 수:* {total_calendar_count}"
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
                                "text": f"*전체 생성된 기록 수:* {total_morning_diary_count + total_evening_diary_count + total_calendar_count + total_memo_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*전체 공유 게시물 조회 수:* {total_share_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*탈퇴한 유저 수:* {withdraw_users_count}"
                            },
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*DAU:* {dau_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*WAU:* {wau_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*MAU:* {mau_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*DAU 증감율:* {dau_growth_rate:.2f}%"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*DAU / MAU:* {dau_to_mau:.2f}%"
                            }
                        ]
                    },
                ]
                # 슬랙에 메세지 보내기
                await client.chat_postMessage(
                    channel=settings.SLACK_ID,
                    blocks=blocks
                )

                # 이미 대쉬보드에 데이터가 있는지 확인
                if dashboards:
                    # 대쉬보드에 데이터가 있으면 업데이트
                    dashboards.today_user = today_users_count
                    dashboards.today_record = total_count
                    dashboards.today_cost = total_cost
                    dashboards.today_dream = morning_diary_count
                    dashboards.today_diary = evening_diary_count
                    dashboards.today_calendar = calender_count
                    dashboards.today_memo = memo_count
                    dashboards.today_mean_request = mean_request
                    dashboards.create_date = now
                    dashboards.dau = dau_count
                    dashboards.wau = wau_count
                    dashboards.mau = mau_count
                    dashboards.dau_to_mau = dau_to_mau
                    dashboards.dau_to_wau = dau_to_wau
                    dashboards.error_count = today_error_count
                    save_db(dashboards, self.db)

                # 대쉬보드에 데이터가 없으면 생성
                else:
                    save = Dashboard(
                        create_date=now,
                        today_user=today_users_count,
                        today_record=total_count,
                        today_cost=total_cost,
                        today_dream=morning_diary_count,
                        today_diary=evening_diary_count,
                        today_calendar=calender_count,
                        today_memo=memo_count,
                        today_mean_request=mean_request,
                        dau=dau_count,
                        wau=wau_count,
                        mau=mau_count,
                        dau_to_mau=dau_to_mau,
                        dau_to_wau=dau_to_wau,
                        error_count=today_error_count
                    )
                    save_db(save, self.db)
            except SlackApiError as e:
                print(f"Error posting message: {e}")


        lock_key = "slack_bot_lock"
        if await self.redis.set(lock_key, "locked", ex=60, nx=True):
            try:
                await slack_bot()
            finally:
                self.db.close()
                await self.redis.delete(lock_key)