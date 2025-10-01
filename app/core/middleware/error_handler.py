import logging
import traceback

from fastapi import Request, status
from fastapi.exception_handlers import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except AppError as ae:
            # Known app error → client-friendly
            logger.error(f"AppError: {ae.detail}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=ae.status_code,
                content={"error": ae.detail},
            )

        except RequestValidationError as ve:
            # FastAPI validation error
            logger.warning(f"Validation error: {ve.errors()}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"error": "Invalid input", "details": ve.errors()},
            )

        except Exception as e:
            # Unknown/unexpected error
            logger.critical(f"Unhandled exception: {e}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal Server Error"},
            )
