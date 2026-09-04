from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PaymentAttemptRequest(BaseModel):
    card_token: str = Field(
        ...,
        description="Mock card token: tok_success, tok_insufficient_funds, tok_card_declined, tok_timeout, tok_network_error"
    )


class PaymentAttemptResponse(BaseModel):
    payment_attempt_id: str
    invoice_id: str
    amount_cents: int
    currency: str = "USD"
    status: str
    invoice_state: str
    psp_reference: Optional[str] = None
    failure_code: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentAttemptListItem(BaseModel):
    id: str
    invoice_id: str
    amount_cents: int
    currency: str
    status: str
    card_token: str
    psp_reference: Optional[str] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
