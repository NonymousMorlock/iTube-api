import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(levelname)s [%(asctime)s] %(name)s - %(message)s",
        },
        "detailed": {
            "format": "%(levelname)s [%(asctime)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "uvicorn": {"level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"level": "INFO"},
        "sqlalchemy.engine": {"level": "WARNING"},
    },
}


def setup_logging():
    """Initialise logging with our config"""
    logging.config.dictConfig(LOGGING_CONFIG)
