from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import time_now
from app.core.status_code import CUSTOM_EXCEPTIONS
from app.db.database import get_SessionLocal
from app.db.models import ErrorLog
from app.schemas.response import ApiResponse
from fastapi.exceptions import RequestValidationError
from slack_sdk.web.async_client import AsyncWebClient

def register_exception_handlers(app):
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        if exc.detail not in CUSTOM_EXCEPTIONS:
            exc.detail = 4000
        SessionLocal = get_SessionLocal()
        db = SessionLocal()
        try:
            error = ErrorLog(error_code=exc.detail, error_message=CUSTOM_EXCEPTIONS[exc.detail], create_date=await time_now())
            db.add(error)
            db.commit()
            db.refresh(error)
            client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
            await client.chat_postMessage(
                channel="C064ZCNDVU1",
                text=f"Error Code: {exc.detail}\nError Message: {CUSTOM_EXCEPTIONS[exc.detail]}"
            )
        except:
            db.rollback()
        finally:
            db.close()
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