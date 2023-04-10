from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.routers import gpt, auth
from app.schemas.common import ApiResponse
from app.core.timing_middleware import TimingMiddleware

app = FastAPI()

app.include_router(auth.router)
app.include_router(gpt.router)
app.add_middleware(TimingMiddleware)

@app.get("/", response_model=ApiResponse)
async def root():
    return ApiResponse(success=True, data={"message": "Hello World"})

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content=ApiResponse(success=False, error=exc.detail).dict(),
        status_code=exc.status_code,
    )
