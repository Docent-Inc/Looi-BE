from app.core.handler import register_exception_handlers, TimeoutMiddleware
from fastapi import FastAPI
from app.routers import auth, report, diary, today, admin, chat
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
app.include_router(report.router)
app.include_router(diary.router)
app.include_router(admin.router)
app.add_middleware(TimingMiddleware)
register_exception_handlers(app)
app.add_middleware(TimeoutMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)