from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import time_now
from app.core.status_code import CUSTOM_EXCEPTIONS
from app.db.database import get_SessionLocal, get_db, save_db
from app.db.models import ErrorLog
from app.schemas.response import ApiResponse
from fastapi.exceptions import RequestValidationError
from slack_sdk.web.async_client import AsyncWebClient

def register_exception_handlers(app):
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        if exc.detail not in CUSTOM_EXCEPTIONS:
            exc.detail = 4000
        if exc.detail == 4220:
            pass
        elif exc.detail == 4998:
            pass
        elif exc.detail == 4004:
            pass
        elif exc.detail == 4506:
            pass
        elif exc.detail == 4005:
            pass
        elif exc.detail == 4010:
            pass
        elif exc.detail == 4221:
            pass
        else:
            if settings.SERVER_TYPE == "prod":
                try:
                    db = next(get_db())
                    error = ErrorLog(error_code=exc.detail, error_message=CUSTOM_EXCEPTIONS[exc.detail], create_date=await time_now())
                    save_db(error, db)
                    client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
                    await client.chat_postMessage(
                        channel="C064ZCNDVU1",
                        text=f"Error Code: {exc.detail}\nError Message: {CUSTOM_EXCEPTIONS[exc.detail]}"
                    )
                except:
                    pass
                finally:
                    db.close()
            else:
                pass
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
        print(request)
        return JSONResponse(
            content=ApiResponse(
                success=False,
                status_code=4999,
                message=CUSTOM_EXCEPTIONS[4999],
            ).dict(),
            status_code=400
        )