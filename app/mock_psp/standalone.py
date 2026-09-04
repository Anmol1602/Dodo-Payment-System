from fastapi import FastAPI, Response, status
from pydantic import BaseModel, Field
import asyncio
import uuid
from typing import Optional

app = FastAPI(
    title="Dodo Payments - Mock Payment Service Provider",
    description="Standalone mock PSP microservice for processing card tokens",
    version="1.0.0"
)


class MockChargeRequest(BaseModel):
    card_token: str = Field(..., description="Card token determining outcome")
    amount_cents: int = Field(..., ge=1, description="Amount in cents")
    currency: str = Field(default="USD")
    invoice_id: Optional[str] = None


@app.post("/charge", status_code=status.HTTP_200_OK)
@app.post("/mock-psp/charge", status_code=status.HTTP_200_OK)
async def process_charge(payload: MockChargeRequest, response: Response):
    token = payload.card_token.strip()

    if token == "tok_success":
        await asyncio.sleep(0.1)
        return {
            "status": "succeeded",
            "psp_ref": str(uuid.uuid4()),
            "amount_cents": payload.amount_cents
        }
    elif token == "tok_insufficient_funds":
        await asyncio.sleep(0.1)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "status": "failed",
            "code": "insufficient_funds",
            "amount_cents": payload.amount_cents
        }
    elif token == "tok_card_declined":
        await asyncio.sleep(0.1)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "status": "failed",
            "code": "card_declined",
            "amount_cents": payload.amount_cents
        }
    elif token == "tok_timeout":
        await asyncio.sleep(30.0)
        return {
            "status": "succeeded",
            "psp_ref": str(uuid.uuid4()),
            "amount_cents": payload.amount_cents
        }
    elif token == "tok_network_error":
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "Simulated PSP connection drop"}
    else:
        await asyncio.sleep(0.1)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "status": "failed",
            "code": "invalid_card_token",
            "amount_cents": payload.amount_cents
        }
