from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.core.database import init_db
from app.core.error_handlers import register_exception_handlers
from app.core.logging_config import setup_logging
from app.core.middleware import AccessLogMiddleware


def create_app():
    setup_logging()
    api = FastAPI()

    api.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_headers=['*'],
        allow_methods=['*'],
        allow_origins=['*'],
    )
    api.add_middleware(AccessLogMiddleware)

    register_exception_handlers(api)

    init_db()

    api.include_router(router=auth_router, prefix="/api/v1")

    return api


app = create_app()
