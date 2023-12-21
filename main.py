from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.handler import register_exception_handlers
from fastapi import FastAPI
from app.db.database import get_db, get_redis_client
from app.routers import auth, report, diary, today, admin, chat, memo, dream, calendar, statistics
from app.core.middleware import TimingMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.service.admin import AdminService
from app.service.report import ReportService

app = FastAPI(title="Look API",
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
app.include_router(report.router)
app.include_router(admin.router)
register_exception_handlers(app)
app.add_middleware(TimingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.SERVER_TYPE == "local":
    scheduler = AsyncIOScheduler()
    @app.on_event("startup")
    async def start_scheduler():
        report_service = ReportService(db=next(get_db()), redis=await get_redis_client())
        scheduler.add_job(
            report_service.generate,
            trigger=CronTrigger(day_of_week='sun', hour=17, minute=0),
            timezone="Asia/Seoul"
        )

        # AdminService 작업 스케줄링
        admin_service = AdminService(db=next(get_db()), redis=await get_redis_client())
        scheduler.add_job(
            admin_service.slack_bot,
            trigger=CronTrigger(minute=59, second=55),
            timezone="Asia/Seoul"
        )

        # 스케줄러 시작 (한 번만 호출)
        scheduler.start()

    @app.on_event("shutdown")
    async def shutdown_report_scheduler():
        scheduler.shutdown()
