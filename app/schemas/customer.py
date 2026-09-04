from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class CustomerCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class CustomerResponse(BaseModel):
    id: str
    business_id: str
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
