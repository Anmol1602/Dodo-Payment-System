from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError, MissingIdempotencyKeyError
from app.models.business import Business
from app.models.payment import PaymentAttempt
from app.models.invoice import Invoice
from app.schemas.payment import PaymentAttemptRequest, PaymentAttemptResponse, PaymentAttemptListItem
from app.services.payment_service import PaymentService
from app.api.deps import get_current_business

router = APIRouter(prefix="/invoices", tags=["Payments"])


@router.post("/{invoice_id}/pay", response_model=PaymentAttemptResponse, status_code=status.HTTP_200_OK)
async def pay_invoice(
    invoice_id: str,
    payload: PaymentAttemptRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """
    Attempts payment for an invoice with a mock card token.
    Must provide 'Idempotency-Key' header for duplicate transaction protection.
    """
    if not idempotency_key or not idempotency_key.strip():
        raise MissingIdempotencyKeyError()

    status_code, response_data = await PaymentService.process_payment(
        session=db,
        business_id=business.id,
        invoice_id=invoice_id,
        card_token=payload.card_token.strip(),
        idempotency_key=idempotency_key.strip(),
        request_path=request.url.path
    )

    return response_data


@router.get("/{invoice_id}/payment-attempts", response_model=List[PaymentAttemptListItem])
async def list_payment_attempts(
    invoice_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Lists all historical payment attempts for an invoice."""
    # Verify invoice belongs to business
    invoice_query = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.business_id == business.id
    )
    inv_res = await db.execute(invoice_query)
    if not inv_res.scalar_one_or_none():
        raise ResourceNotFoundError("Invoice", invoice_id)

    query = (
        select(PaymentAttempt)
        .where(PaymentAttempt.invoice_id == invoice_id)
        .order_by(PaymentAttempt.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
