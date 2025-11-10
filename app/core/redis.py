# app/redis.py
import logging

from redis import Redis, exceptions

from app.core.config import settings
from app.core.exceptions import InternalServerError

logger = logging.getLogger(__name__)

# This will hold the singleton client instance
_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """
    Dependency function to get a singleton Redis client.

    This function will initialize the client on its first call and
    return the same instance on all subsequent calls.
    """
    global _redis_client

    # If the client isn't initialized, create it
    if _redis_client is None:
        logger.info("Initializing Redis client...")
        try:
            client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=5
            )
            client.ping()
            _redis_client = client  # Set the global instance
            logger.info(
                '✅ Redis Connected successfully to %s:%s',
                settings.REDIS_HOST, settings.REDIS_PORT
            )

        except exceptions.ConnectionError as e:
            logger.error('❌ Redis Connection Error: %s', e, exc_info=True)
            # This will raise a 500 error on the request that
            # first tries to use Redis, but it won't crash the app on startup.
            raise InternalServerError('Could not connect to Redis service') from e

    return _redis_client
