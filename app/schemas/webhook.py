from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, HttpUrl, Field


class WebhookEndpointCreateRequest(BaseModel):
    url: str = Field(..., description="HTTPS callback URL")


class WebhookEndpointResponse(BaseModel):
    id: str
    business_id: str
    url: str
    secret: str = Field(..., description="Secret used to sign HMAC-SHA256 headers")
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookEventPayload(BaseModel):
    id: str
    event: str  # invoice.created, invoice.paid, invoice.payment_failed
    timestamp: int
    data: Dict[str, Any]


class WebhookDeliveryResponse(BaseModel):
    id: str
    endpoint_id: str
    event_type: str
    status: str
    attempt_count: int
    last_status_code: Optional[int] = None
    last_error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
