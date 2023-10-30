from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.routers import auth, generate, diary, kakao_chatbot, today, admin
from app.core.status_code import CUSTOM_EXCEPTIONS
from app.schemas.response import ApiResponse
from app.core.middleware import TimingMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

app = FastAPI(title="Docent API",
              description="도슨트 서비스 API 문서입니다.",
              version="0.2.0",
              docs_url='/docs',
              redoc_url='/redoc',
              root_path="/api",
              openapi_url='/openapi.json')

app.include_router(auth.router)
app.include_router(generate.router)
app.include_router(diary.router)
app.include_router(today.router)
# app.include_router(kakao_chatbot.router)
app.include_router(admin.router)
app.add_middleware(TimingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.detail not in CUSTOM_EXCEPTIONS:
        exc.detail = 4000
    return JSONResponse(
        content=ApiResponse(
            success=False,
            status_code=exc.detail,
            message=CUSTOM_EXCEPTIONS[exc.detail],
        ).dict(),
        status_code=exc.status_code
    )
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        content=ApiResponse(
            success=False,
            status_code=4999,
            message=CUSTOM_EXCEPTIONS[4999],
        ).dict(),
        status_code=400
    )
