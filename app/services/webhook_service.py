import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.security import sign_webhook_payload
from app.models.webhook import WebhookEndpoint, WebhookDelivery

logger = logging.getLogger("webhook_service")


class WebhookService:
    """
    Manages webhook signing, non-blocking asynchronous dispatch, and retry backoff.
    Guarantees:
      1. Cryptographic HMAC-SHA256 signature in X-Dodo-Signature header
      2. Replay attack prevention via timestamp header
      3. Non-blocking dispatch (API responses never wait for receiver network I/O)
      4. Exponential backoff retry on failed attempts
    """

    @classmethod
    async def dispatch_event(
        cls,
        business_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Dispatches an event in a fire-and-forget background task.
        Safe against unhandled exceptions.
        """
        asyncio.create_task(
            cls._deliver_to_endpoints(business_id, event_type, event_data)
        )

    @classmethod
    async def _deliver_to_endpoints(
        cls,
        business_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        async with async_session_factory() as session:
            try:
                # Find all active webhook endpoints for this business
                query = select(WebhookEndpoint).where(
                    WebhookEndpoint.business_id == business_id,
                    WebhookEndpoint.is_active == True
                )
                result = await session.execute(query)
                endpoints = result.scalars().all()

                if not endpoints:
                    return

                timestamp = int(time.time())
                payload_dict = {
                    "event": event_type,
                    "timestamp": timestamp,
                    "business_id": business_id,
                    "data": event_data
                }
                payload_json = json.dumps(payload_dict, default=str)
                payload_bytes = payload_json.encode("utf-8")

                for endpoint in endpoints:
                    delivery = WebhookDelivery(
                        endpoint_id=endpoint.id,
                        event_type=event_type,
                        payload=payload_dict,
                        status="pending",
                        attempt_count=0
                    )
                    session.add(delivery)
                    await session.flush()

                    # Deliver with exponential retry
                    await cls._execute_delivery_with_retries(
                        delivery_id=delivery.id,
                        endpoint_url=endpoint.url,
                        secret=endpoint.secret,
                        payload_bytes=payload_bytes,
                        payload_dict=payload_dict,
                        event_type=event_type,
                        timestamp=timestamp
                    )

                await session.commit()
            except Exception as e:
                logger.error(f"Error executing webhook dispatch for business {business_id}: {e}")
                await session.rollback()

    @classmethod
    async def _execute_delivery_with_retries(
        cls,
        delivery_id: str,
        endpoint_url: str,
        secret: str,
        payload_bytes: bytes,
        payload_dict: Dict[str, Any],
        event_type: str,
        timestamp: int
    ) -> None:
        signature_header = sign_webhook_payload(secret, payload_bytes, timestamp)
        headers = {
            "Content-Type": "application/json",
            "X-Dodo-Signature": signature_header,
            "X-Dodo-Event": event_type,
            "User-Agent": "Dodo-Webhook-Dispatcher/1.0",
        }

        # Attempt immediate delivery, retry with exponential backoff if failed
        for attempt in range(1, settings.WEBHOOK_MAX_RETRIES + 1):
            try:
                timeout = httpx.Timeout(settings.WEBHOOK_TIMEOUT_SECONDS)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(endpoint_url, content=payload_bytes, headers=headers)
                    if 200 <= resp.status_code < 300:
                        await cls._update_delivery_status(delivery_id, "delivered", attempt, resp.status_code, None)
                        return
                    else:
                        error_msg = f"Receiver returned status HTTP {resp.status_code}"
                        await cls._update_delivery_status(delivery_id, "failed", attempt, resp.status_code, error_msg)

            except Exception as ex:
                error_msg = f"Connection error: {str(ex)}"
                await cls._update_delivery_status(delivery_id, "failed", attempt, None, error_msg)

            # If not the final attempt, sleep for exponential backoff: (2 ** attempt) * base
            if attempt < settings.WEBHOOK_MAX_RETRIES:
                backoff_seconds = min((2 ** attempt) * settings.WEBHOOK_BASE_BACKOFF_SECONDS, 300.0)
                # In testing/local, keep sleep brief
                if settings.ENVIRONMENT == "test":
                    backoff_seconds = 0.05
                await asyncio.sleep(backoff_seconds)

    @classmethod
    async def _update_delivery_status(
        cls,
        delivery_id: str,
        status_str: str,
        attempt_count: int,
        status_code: int | None,
        error_msg: str | None
    ) -> None:
        async with async_session_factory() as session:
            try:
                delivery = await session.get(WebhookDelivery, delivery_id)
                if delivery:
                    delivery.status = status_str
                    delivery.attempt_count = attempt_count
                    delivery.last_status_code = status_code
                    delivery.last_error = error_msg
                    if status_str == "failed":
                        delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=15 * attempt_count)
                    await session.commit()
            except Exception as e:
                logger.error(f"Failed to record webhook delivery status: {e}")
                await session.rollback()
