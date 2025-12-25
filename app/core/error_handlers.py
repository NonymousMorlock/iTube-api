import logging

from fastapi import HTTPException
from fastapi import Request, status, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.error_response import ErrorResponse
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _on_validation_error(request: Request, exc: RequestValidationError):
        logger.warning("422 %s %s :: %s", request.method, request.url, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(error="Invalid input", details=exc.errors()).model_dump(),
        )

    @app.exception_handler(AppError)
    async def _on_app_error(request: Request, exc: AppError):
        logger.error("AppError %s %s :: %s", request.method, request.url, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=exc.error_code or str(exc.status_code), details=exc.detail).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def _on_http_exc(request: Request, exc: HTTPException):
        logger.warning("HTTPException %s %s :: %s", request.method, request.url, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=str(exc.detail)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def _on_uncaught(request: Request, exc: Exception):
        logger.critical("Unhandled %s %s", request.method, request.url, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(error="Internal Server Error").model_dump(),
        )
