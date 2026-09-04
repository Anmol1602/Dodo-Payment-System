from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class LineItemCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., ge=1, description="Must be an integer >= 1")
    unit_amount_cents: int = Field(..., ge=0, description="Unit price in integer cents (no floats)")


class LineItemResponse(BaseModel):
    id: str
    description: str
    quantity: int
    unit_amount_cents: int
    total_amount_cents: int

    class Config:
        from_attributes = True


class InvoiceCreateRequest(BaseModel):
    customer_id: str = Field(..., description="UUID of customer")
    due_date: date
    auto_finalize: bool = Field(default=True, description="If true, transition immediately from draft to open")
    line_items: List[LineItemCreate] = Field(..., min_length=1, description="At least one line item required")

    @field_validator("line_items")
    @classmethod
    def validate_line_items(cls, v: List[LineItemCreate]) -> List[LineItemCreate]:
        if not v:
            raise ValueError("Invoice must contain at least one line item")
        return v


class InvoiceResponse(BaseModel):
    id: str
    business_id: str
    customer_id: str
    state: str
    currency: str = "USD"
    total_amount_cents: int
    due_date: date
    line_items: List[LineItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceFilterParams(BaseModel):
    state: Optional[str] = None
    customer_id: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
