from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.handler import register_exception_handlers
from fastapi import FastAPI
from app.db.database import get_db, get_redis_client
from app.routers import auth, report, diary, today, admin, chat, memo, dream, calendar, statistics, share, push
from app.core.middleware import TimingMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.service.admin import AdminService
from app.service.push import PushService

app = FastAPI(title="Looi API",
              version="0.2.0",
              docs_url='/docs',
              redoc_url='/redoc',
              root_path=settings.ROOT_PATH,
              openapi_url='/openapi.json')

app.include_router(auth.router)
app.include_router(today.router)
app.include_router(chat.router)
app.include_router(statistics.router)
app.include_router(dream.router)
app.include_router(diary.router)
app.include_router(memo.router)
app.include_router(calendar.router)
app.include_router(share.router)
app.include_router(report.router)
app.include_router(admin.router)
app.include_router(push.router)
register_exception_handlers(app)
app.add_middleware(TimingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.SERVER_TYPE == "prod":
    scheduler = AsyncIOScheduler()
    @app.on_event("startup")
    async def start_scheduler():
        # AdminService 작업 스케줄링 1시간마다 실행, 슬렉 알림
        scheduler.add_job(
            AdminService(db=next(get_db()), redis=next(get_redis_client())).slack_bot,
            trigger=CronTrigger(minute=59, second=55, timezone="Asia/Seoul"),
        )

        # PushService 작업 스케줄링
        scheduler.add_job(
            PushService(db=next(get_db()), redis=next(get_redis_client())).send_morning_push,
            trigger=CronTrigger(hour=8, timezone="Asia/Seoul"),
        )

        scheduler.add_job(
            PushService(db=next(get_db()), redis=next(get_redis_client())).send_afternoon_push,
            trigger=CronTrigger(hour=14, timezone="Asia/Seoul"),
        )

        scheduler.add_job(
            PushService(db=next(get_db()), redis=next(get_redis_client())).send_night_push,
            trigger=CronTrigger(hour=22, timezone="Asia/Seoul"),
        )

        scheduler.add_job(
            PushService(db=next(get_db()), redis=next(get_redis_client())).generate_night_push,
            trigger=CronTrigger(hour=21, timezone="Asia/Seoul"),
        )

        scheduler.add_job(
            PushService(db=next(get_db()), redis=next(get_redis_client())).push_schedule,
            trigger=CronTrigger(second=0, timezone="Asia/Seoul"),
        )

        # 스케줄러 시작 (한 번만 호출)
        scheduler.start()

    @app.on_event("shutdown")
    async def shutdown_report_scheduler():
        scheduler.shutdown()
