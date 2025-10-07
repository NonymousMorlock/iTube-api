from pydantic import BaseModel
from typing import Any, List, Dict

class ErrorResponse(BaseModel):
    error: str
    details: Any | List | Dict |None = None
    request_id: str | None = None
