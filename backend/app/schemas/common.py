from typing import Any, Optional, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class APIResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
