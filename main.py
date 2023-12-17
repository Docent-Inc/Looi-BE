import aiocron
import pytz

from app.core.handler import register_exception_handlers
from fastapi import FastAPI

from app.feature.report import generate
from app.feature.slackBot import scheduled_task
from app.routers import auth, report, diary, today, admin, chat, memo, dream, calendar, statistics
from app.core.middleware import TimingMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


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
    cron_task = aiocron.crontab('14 20 * * 0', func=generate, start=False, tz=pytz.timezone('Asia/Seoul'))
    cron_task.start()

    cron_task = aiocron.crontab('59 23 * * *', func=scheduled_task, start=False, tz=pytz.timezone('Asia/Seoul'))
    cron_task.start()
