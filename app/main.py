from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging_config import setup_logging
from app.middleware.error_handler import ErrorHandlerMiddleware


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
    api.add_middleware(ErrorHandlerMiddleware)
    return api

app = create_app()
