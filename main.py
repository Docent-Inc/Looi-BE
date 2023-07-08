from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.routers import auth, generate, diary, search, mvp, line_chatbot, kakao_chatbot
from app.schemas.common import ApiResponse
from app.core.middleware import TimingMiddleware, LogRequestBodyMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(auth.router)
app.include_router(generate.router)
app.include_router(diary.router)
app.include_router(search.router)
app.include_router(mvp.router)
app.include_router(line_chatbot.router)
app.include_router(kakao_chatbot.router)
app.add_middleware(TimingMiddleware)
app.add_middleware(LogRequestBodyMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content=ApiResponse(success=False, error=exc.detail).dict(),
        status_code=exc.status_code,
    )
