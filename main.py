from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.routers import auth, generate, diary, kakao_chatbot, today
from app.schemas.response import ApiResponse
from app.core.middleware import TimingMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

CUSTOM_EXCEPTIONS = {
    4000: "알 수 없는 에러가 발생했습니다.",
    4001: "이메일 주소가 이미 존재합니다.",
    4002: "닉네임이 이미 존재합니다.",
    4003: "이메일 또는 비밀번호가 일치하지 않습니다.",
    4004: "refresh_token이 유효하지 않습니다.",
    4005: "사용자가 존재하지 않습니다.",
    4006: "비밀번호가 일치하지 않습니다.",
    4007: "새로운 비밀번호를 입력해주세요.",
    4008: "중복된 닉네임입니다. 다른 닉네임을 입력해주세요.",
    4009: "올바르지 않은 MBTI입니다.",
    4010: "카카오톡에서 회원정보를 불러오는 중 오류가 발생했습니다.",
    4011: "morning diary가 존재하지 않습니다.",
    4012: "night diary가 존재하지 않습니다.",
    4013: "택스트 분류를 실패했습니다.",
    4014: "일정 생성에 실패했습니다.",
    4015: "일정 조회에 실패했습니다.",
    4016: "메모 조회에 실패했습니다.",
    4017: "마음 보고서 생성에 실패했습니다.",
    4018: "이번주 마음 보고서가 이미 존재합니다.",
    4019: "마음 보고서를 만들기 위한 기록이 부족합니다.",

    4220: "jwt 토큰이 필요합니다.",
    4500: "이미지 정보를 불러오는데 실패했습니다.",
    4501: "Chat GPT API 호출에 실패했습니다.",
    4502: "NaverClova API 호출에 실패했습니다.",
    4503: "Stable Diffusion API 호출에 실패했습니다.",
    4504: "Karlo2 API 호출에 실패했습니다.",
    4505: "Dalle2 API 호출에 실패했습니다.",
    4999: "요청 유효성 검사에 실패했습니다.",
    5000: "서버에 문제가 발생했습니다.",
}

app = FastAPI(openapi_url="/v1/openapi.json")

app.include_router(auth.router)
app.include_router(generate.router)
app.include_router(diary.router)
app.include_router(today.router)
# app.include_router(kakao_chatbot.router)
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
