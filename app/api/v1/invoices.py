from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.business import Business
from app.schemas.invoice import InvoiceCreateRequest, InvoiceResponse
from app.services.invoice_service import InvoiceService
from app.api.deps import get_current_business

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreateRequest,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates an invoice with line items.
    The server calculates the total in integer cents. Client-supplied totals are never trusted.
    """
    invoice = await InvoiceService.create_invoice(
        session=db,
        business_id=business.id,
        data=payload
    )
    return invoice


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(
    state: Optional[str] = Query(None, description="Filter by state: draft, open, paid, void, uncollectible"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Lists invoices for the business, filterable by state and customer."""
    invoices = await InvoiceService.list_invoices(
        session=db,
        business_id=business.id,
        state=state,
        customer_id=customer_id,
        limit=limit,
        offset=offset
    )
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves an invoice by ID (scoped to business) with line items."""
    invoice = await InvoiceService.get_invoice_by_id(
        session=db,
        business_id=business.id,
        invoice_id=invoice_id
    )
    return invoice


@router.post("/{invoice_id}/finalize", response_model=InvoiceResponse)
async def finalize_invoice(
    invoice_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Finalizes a draft invoice, transitioning it to open."""
    return await InvoiceService.finalize_invoice(
        session=db,
        business_id=business.id,
        invoice_id=invoice_id
    )


@router.post("/{invoice_id}/void", response_model=InvoiceResponse)
async def void_invoice(
    invoice_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Voids an invoice. Terminal state."""
    return await InvoiceService.void_invoice(
        session=db,
        business_id=business.id,
        invoice_id=invoice_id
    )


@router.post("/{invoice_id}/mark-uncollectible", response_model=InvoiceResponse)
async def mark_invoice_uncollectible(
    invoice_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Marks an open invoice as uncollectible (bad debt)."""
    return await InvoiceService.mark_uncollectible(
        session=db,
        business_id=business.id,
        invoice_id=invoice_id
    )
