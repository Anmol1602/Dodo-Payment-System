from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
