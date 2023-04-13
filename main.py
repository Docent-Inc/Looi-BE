from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.routers import gpt, auth
from app.schemas.common import ApiResponse
from app.core.timing_middleware import TimingMiddleware
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(auth.router)
app.include_router(gpt.router)
app.add_middleware(TimingMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=ApiResponse)
async def root():
    return ApiResponse(success=True, data={"message": "Hello World"})

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content=ApiResponse(success=False, error=exc.detail).dict(),
        status_code=exc.status_code,
    )
