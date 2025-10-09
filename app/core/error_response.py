from typing import Any, List, Dict

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    details: Any | List | Dict | None = None
    request_id: str | None = None
