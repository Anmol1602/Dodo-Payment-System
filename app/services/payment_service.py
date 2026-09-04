import hashlib
import json
from typing import Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import (
    ResourceNotFoundError,
    IdempotencyConflictError,
    PaymentFailedError,
    PSPTimeoutError,
    PSPNetworkError,
    InvalidStateTransitionError,
)
from app.models.invoice import Invoice
from app.models.payment import PaymentAttempt
from app.models.idempotency import IdempotencyRecord
from app.state_machine.invoice_state import InvoiceStateMachine, InvoiceState
from app.services.psp_client import psp_client
from app.services.webhook_service import WebhookService


class PaymentService:
    @classmethod
    async def process_payment(
        cls,
        session: AsyncSession,
        business_id: str,
        invoice_id: str,
        card_token: str,
        idempotency_key: str,
        request_path: str,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Executes an idempotent payment attempt against the invoice.
        Guarantees:
          1. Atomicity: uses row-level locking (with_for_update) to prevent race conditions
          2. Idempotency: replaying an identical key returns the cached response
          3. Resilience: slow/failed PSP calls do not corrupt the invoice state
        """
        request_body_dict = {"card_token": card_token}
        request_hash = hashlib.sha256(
            json.dumps(request_body_dict, sort_keys=True).encode("utf-8")
        ).hexdigest()

        # Step 1: Check Idempotency Record
        idemp_query = select(IdempotencyRecord).where(
            IdempotencyRecord.business_id == business_id,
            IdempotencyRecord.idempotency_key == idempotency_key
        )
        idemp_result = await session.execute(idemp_query)
        existing_record = idemp_result.scalar_one_or_none()

        if existing_record:
            if existing_record.request_hash != request_hash:
                raise IdempotencyConflictError(
                    key=idempotency_key,
                    message="Idempotency key reused with a different request payload."
                )
            # Replay stored response
            return existing_record.response_status, existing_record.response_body

        # Step 2: Lock the Invoice row and verify state
        # In PostgreSQL: select ... with_for_update() ensures sequential payment evaluation
        invoice_query = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.business_id == business_id
        ).with_for_update()
        invoice_result = await session.execute(invoice_query)
        invoice = invoice_result.scalar_one_or_none()

        if not invoice:
            raise ResourceNotFoundError("Invoice", invoice_id)

        # Assert invoice can accept payments (must be 'open')
        InvoiceStateMachine.assert_can_pay(invoice.state)

        # Step 3: Insert initial PaymentAttempt in 'pending' state
        attempt = PaymentAttempt(
            invoice_id=invoice.id,
            business_id=business_id,
            amount_cents=invoice.total_amount_cents,
            currency="USD",
            status="pending",
            card_token=card_token,
            idempotency_key=idempotency_key
        )
        session.add(attempt)
        await session.flush()

        # Step 4: Call external Mock PSP over HTTP
        psp_result = await psp_client.charge(
            card_token=card_token,
            amount_cents=invoice.total_amount_cents,
            invoice_id=invoice.id,
            currency="USD"
        )

        response_status = 200
        response_body: Dict[str, Any] = {}

        # Step 5: Handle PSP outcome deterministically
        if psp_result.status == "succeeded":
            attempt.status = "succeeded"
            attempt.psp_reference = psp_result.psp_ref

            # Transition invoice state machine: OPEN -> PAID (terminal)
            invoice.state = InvoiceStateMachine.transition(
                invoice.state, InvoiceState.PAID, action="pay"
            ).value

            response_body = {
                "payment_attempt_id": attempt.id,
                "invoice_id": invoice.id,
                "amount_cents": attempt.amount_cents,
                "currency": attempt.currency,
                "status": "succeeded",
                "invoice_state": invoice.state,
                "psp_reference": attempt.psp_reference,
                "failure_code": None,
                "created_at": attempt.created_at.isoformat(),
            }
            response_status = 200

            # Store idempotency record
            await cls._save_idempotency(session, business_id, idempotency_key, request_path, request_hash, response_status, response_body)
            await session.commit()

            # Dispatch invoice.paid webhook
            await WebhookService.dispatch_event(
                business_id=business_id,
                event_type="invoice.paid",
                event_data={
                    "invoice_id": invoice.id,
                    "payment_attempt_id": attempt.id,
                    "amount_cents": attempt.amount_cents,
                    "psp_reference": attempt.psp_reference,
                }
            )
            return response_status, response_body

        elif psp_result.status == "failed":
            attempt.status = "failed"
            attempt.failure_code = psp_result.failure_code
            attempt.failure_message = psp_result.failure_message
            # Invoice remains in OPEN state so customer can retry
            invoice.state = InvoiceState.OPEN.value

            response_body = {
                "error": {
                    "code": "PAYMENT_FAILED",
                    "message": f"Payment declined by processor: {psp_result.failure_code}",
                    "payment_attempt_id": attempt.id,
                    "invoice_id": invoice.id,
                    "failure_code": psp_result.failure_code,
                    "invoice_state": invoice.state,
                }
            }
            response_status = 402

            await cls._save_idempotency(session, business_id, idempotency_key, request_path, request_hash, response_status, response_body)
            await session.commit()

            # Dispatch invoice.payment_failed webhook
            await WebhookService.dispatch_event(
                business_id=business_id,
                event_type="invoice.payment_failed",
                event_data={
                    "invoice_id": invoice.id,
                    "payment_attempt_id": attempt.id,
                    "amount_cents": attempt.amount_cents,
                    "failure_code": psp_result.failure_code,
                }
            )

            raise PaymentFailedError(
                failure_code=psp_result.failure_code or "declined",
                message=f"Payment declined by processor: {psp_result.failure_code}",
                payment_attempt_id=attempt.id,
                invoice_id=invoice.id,
                invoice_state=invoice.state
            )

        elif psp_result.status == "timeout":
            # Handled timeout: tok_timeout sleeps 30s.
            # Client timed out safely after 5s. Invoice state is preserved as OPEN!
            attempt.status = "pending"
            attempt.failure_code = "timeout"
            attempt.failure_message = psp_result.failure_message

            response_body = {
                "error": {
                    "code": "PSP_TIMEOUT",
                    "message": "Payment processor timed out. Payment attempt recorded in pending state.",
                    "payment_attempt_id": attempt.id,
                    "invoice_id": invoice.id,
                    "failure_code": "timeout",
                    "invoice_state": invoice.state,
                }
            }
            response_status = 504

            await cls._save_idempotency(session, business_id, idempotency_key, request_path, request_hash, response_status, response_body)
            await session.commit()

            raise PSPTimeoutError(
                payment_attempt_id=attempt.id,
                invoice_id=invoice.id,
                invoice_state=invoice.state
            )

        else:  # network_error
            attempt.status = "failed"
            attempt.failure_code = "network_error"
            attempt.failure_message = psp_result.failure_message

            response_body = {
                "error": {
                    "code": "PSP_NETWORK_ERROR",
                    "message": "Payment processor network error or connection dropped.",
                    "payment_attempt_id": attempt.id,
                    "invoice_id": invoice.id,
                    "failure_code": "network_error",
                    "invoice_state": invoice.state,
                }
            }
            response_status = 502

            await cls._save_idempotency(session, business_id, idempotency_key, request_path, request_hash, response_status, response_body)
            await session.commit()

            raise PSPNetworkError(
                payment_attempt_id=attempt.id,
                invoice_id=invoice.id,
                invoice_state=invoice.state,
                error_detail=psp_result.failure_message or "Connection error"
            )

    @staticmethod
    async def _save_idempotency(
        session: AsyncSession,
        business_id: str,
        idempotency_key: str,
        request_path: str,
        request_hash: str,
        response_status: int,
        response_body: Dict[str, Any]
    ) -> None:
        rec = IdempotencyRecord(
            business_id=business_id,
            idempotency_key=idempotency_key,
            request_path=request_path,
            request_hash=request_hash,
            response_status=response_status,
            response_body=response_body,
        )
        session.add(rec)
