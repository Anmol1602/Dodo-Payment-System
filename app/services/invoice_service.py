from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import ResourceNotFoundError, InvalidStateTransitionError
from app.models.invoice import Invoice, InvoiceLineItem
from app.models.customer import Customer
from app.schemas.invoice import InvoiceCreateRequest, LineItemCreate
from app.state_machine.invoice_state import InvoiceStateMachine, InvoiceState
from app.services.webhook_service import WebhookService


class InvoiceService:
    @staticmethod
    def calculate_totals(line_items_data: List[LineItemCreate]) -> tuple[int, List[dict]]:
        """
        Computes invoice line items and grand total strictly using integer cents.
        Never trust a client-supplied total.
        """
        grand_total = 0
        computed_items = []

        for item in line_items_data:
            quantity = int(item.quantity)
            unit_amount_cents = int(item.unit_amount_cents)
            item_total = quantity * unit_amount_cents

            if quantity < 1:
                raise ValueError("Line item quantity must be at least 1")
            if unit_amount_cents < 0:
                raise ValueError("Line item unit amount must be non-negative")

            grand_total += item_total
            computed_items.append({
                "description": item.description,
                "quantity": quantity,
                "unit_amount_cents": unit_amount_cents,
                "total_amount_cents": item_total,
            })

        return grand_total, computed_items

    @classmethod
    async def create_invoice(
        cls,
        session: AsyncSession,
        business_id: str,
        data: InvoiceCreateRequest
    ) -> Invoice:
        # Verify customer belongs to this business
        customer = await session.get(Customer, data.customer_id)
        if not customer or customer.business_id != business_id:
            raise ResourceNotFoundError("Customer", data.customer_id)

        # Server-computed grand total in integer cents
        total_amount_cents, items_to_create = cls.calculate_totals(data.line_items)

        initial_state = InvoiceState.OPEN.value if data.auto_finalize else InvoiceState.DRAFT.value

        invoice = Invoice(
            business_id=business_id,
            customer_id=data.customer_id,
            state=initial_state,
            currency="USD",
            total_amount_cents=total_amount_cents,
            due_date=data.due_date,
        )
        session.add(invoice)
        await session.flush()

        for item_data in items_to_create:
            line_item = InvoiceLineItem(
                invoice_id=invoice.id,
                description=item_data["description"],
                quantity=item_data["quantity"],
                unit_amount_cents=item_data["unit_amount_cents"],
                total_amount_cents=item_data["total_amount_cents"],
            )
            session.add(line_item)

        await session.commit()
        await session.refresh(invoice)

        # Emit invoice.created webhook asynchronously
        await WebhookService.dispatch_event(
            business_id=business_id,
            event_type="invoice.created",
            event_data={
                "invoice_id": invoice.id,
                "customer_id": invoice.customer_id,
                "total_amount_cents": invoice.total_amount_cents,
                "state": invoice.state,
                "due_date": str(invoice.due_date),
            }
        )

        return invoice

    @staticmethod
    async def get_invoice_by_id(
        session: AsyncSession,
        business_id: str,
        invoice_id: str
    ) -> Invoice:
        query = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.business_id == business_id
        ).options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.payment_attempts)
        )
        result = await session.execute(query)
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise ResourceNotFoundError("Invoice", invoice_id)
        return invoice

    @staticmethod
    async def list_invoices(
        session: AsyncSession,
        business_id: str,
        state: Optional[str] = None,
        customer_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Invoice]:
        query = select(Invoice).where(
            Invoice.business_id == business_id
        ).options(
            selectinload(Invoice.line_items)
        ).order_by(Invoice.created_at.desc())

        if state:
            query = query.where(Invoice.state == state)
        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)

        query = query.limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def finalize_invoice(
        cls,
        session: AsyncSession,
        business_id: str,
        invoice_id: str
    ) -> Invoice:
        invoice = await cls.get_invoice_by_id(session, business_id, invoice_id)
        new_state = InvoiceStateMachine.transition(invoice.state, InvoiceState.OPEN, action="finalize")
        invoice.state = new_state.value
        await session.commit()
        await session.refresh(invoice)
        return invoice

    @classmethod
    async def void_invoice(
        cls,
        session: AsyncSession,
        business_id: str,
        invoice_id: str
    ) -> Invoice:
        invoice = await cls.get_invoice_by_id(session, business_id, invoice_id)
        new_state = InvoiceStateMachine.transition(invoice.state, InvoiceState.VOID, action="void")
        invoice.state = new_state.value
        await session.commit()
        await session.refresh(invoice)
        return invoice

    @classmethod
    async def mark_uncollectible(
        cls,
        session: AsyncSession,
        business_id: str,
        invoice_id: str
    ) -> Invoice:
        invoice = await cls.get_invoice_by_id(session, business_id, invoice_id)
        new_state = InvoiceStateMachine.transition(invoice.state, InvoiceState.UNCOLLECTIBLE, action="mark_uncollectible")
        invoice.state = new_state.value
        await session.commit()
        await session.refresh(invoice)
        return invoice
