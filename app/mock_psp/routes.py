import asyncio
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/mock-psp", tags=["Mock PSP"])


class MockChargeRequest(BaseModel):
    card_token: str = Field(..., description="Card token determining outcome")
    amount_cents: int = Field(..., ge=1, description="Amount in cents")
    currency: str = Field(default="USD")
    invoice_id: Optional[str] = None


class MockChargeSuccessResponse(BaseModel):
    status: str = "succeeded"
    psp_ref: str
    amount_cents: int


class MockChargeFailedResponse(BaseModel):
    status: str = "failed"
    code: str
    amount_cents: int


@router.post("/charge", status_code=status.HTTP_200_OK)
async def process_mock_charge(payload: MockChargeRequest, response: Response):
    """
    Mock Payment Processor endpoint complying with the technical specification.
    Token Behavior:
      tok_success: Returns {status: "succeeded", psp_ref: <uuid>} after ~100ms
      tok_insufficient_funds: Returns {status: "failed", code: "insufficient_funds"} after ~100ms
      tok_card_declined: Returns {status: "failed", code: "card_declined"} after ~100ms
      tok_timeout: Sleeps 30 seconds then returns success
      tok_network_error: Returns 500 or connection failure
    """
    token = payload.card_token.strip()

    if token == "tok_success":
        await asyncio.sleep(0.1)  # 100ms
        return MockChargeSuccessResponse(
            status="succeeded",
            psp_ref=str(uuid.uuid4()),
            amount_cents=payload.amount_cents
        )

    elif token == "tok_insufficient_funds":
        await asyncio.sleep(0.1)  # 100ms
        response.status_code = status.HTTP_400_BAD_REQUEST
        return MockChargeFailedResponse(
            status="failed",
            code="insufficient_funds",
            amount_cents=payload.amount_cents
        )

    elif token == "tok_card_declined":
        await asyncio.sleep(0.1)  # 100ms
        response.status_code = status.HTTP_400_BAD_REQUEST
        return MockChargeFailedResponse(
            status="failed",
            code="card_declined",
            amount_cents=payload.amount_cents
        )

    elif token == "tok_timeout":
        # Simulates a hanging gateway / processor: sleeps 30 seconds
        await asyncio.sleep(30.0)
        return MockChargeSuccessResponse(
            status="succeeded",
            psp_ref=str(uuid.uuid4()),
            amount_cents=payload.amount_cents
        )

    elif token == "tok_network_error":
        # Returns 500 internal server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulated PSP upstream network connection drop / internal error"
        )

    else:
        # Default unrecognized token behavior: decline
        await asyncio.sleep(0.1)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return MockChargeFailedResponse(
            status="failed",
            code="invalid_card_token",
            amount_cents=payload.amount_cents
        )
