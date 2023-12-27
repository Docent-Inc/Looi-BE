import time
from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        process_time = (end_time - start_time) * 1000  # Convert to milliseconds
        process_time = int(process_time)
        response.headers["X-Process-Time"] = str(process_time) + " ms"
        max_process_time = 60000  # 최대 허용 응답 시간 (밀리초)
        if process_time > max_process_time:
            content = {
                "success": False,
                "status_code": 4997,  # 또는 적절한 에러 코드
                "message": "요청 시간이 초과되었습니다. 다시 시도해주세요."
            }
            return JSONResponse(content=content, status_code=status.HTTP_408_REQUEST_TIMEOUT)
        return response