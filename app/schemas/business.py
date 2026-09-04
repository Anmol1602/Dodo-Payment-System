from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BusinessRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Business name")


class BusinessRegisterResponse(BaseModel):
    business_id: str
    name: str
    api_key: str = Field(..., description="Raw API key. Shown only once.")
    created_at: datetime


class ApiKeyResponse(BaseModel):
    id: str
    key_prefix: str
    label: str
    is_revoked: bool
    created_at: datetime
    revoked_at: Optional[datetime] = None


class ApiKeyCreateRequest(BaseModel):
    label: str = Field(default="API Key", max_length=100)
    is_test: bool = False
