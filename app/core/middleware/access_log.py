import logging
import time

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class AccessLogMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        start = time.perf_counter()

        async def _send(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                method = scope["method"]
                path = scope["path"]
                dur_ms = (time.perf_counter() - start) * 1000
                logger.info("%s %s -> %d in %.1fms", method, path, status_code, dur_ms)
            await send(message)

        return await self.app(scope, receive, _send)
