import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        process_time = (end_time - start_time) * 1000  # Convert to milliseconds
        process_time = int(process_time)
        response.headers["X-Process-Time"] = str(process_time) + " ms"
        return response # 응답시간을 반환하는 미들웨어