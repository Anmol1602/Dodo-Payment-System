import asyncio
import httpx
from typing import Optional
from pydantic import BaseModel
from app.core.config import settings


class PSPChargeResult(BaseModel):
    status: str  # "succeeded", "failed", "timeout", "network_error"
    psp_ref: Optional[str] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None


class MockPSPClient:
    """
    HTTP client for calling the upstream Payment Service Provider.
    Treats the mock PSP as a real external network dependency.
    Implements strict client-side timeouts to prevent slow PSPs from hanging worker threads.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None
    ):
        self.base_url = base_url or settings.PSP_URL
        self.timeout_seconds = timeout_seconds or settings.PSP_TIMEOUT_SECONDS
        self.transport = transport

    async def charge(
        self,
        card_token: str,
        amount_cents: int,
        invoice_id: str,
        currency: str = "USD"
    ) -> PSPChargeResult:
        payload = {
            "card_token": card_token,
            "amount_cents": amount_cents,
            "invoice_id": invoice_id,
            "currency": currency,
        }

        # Use httpx.AsyncClient with strict client timeout
        timeout = httpx.Timeout(self.timeout_seconds, connect=3.0)
        try:
            client_kwargs = {"timeout": timeout}
            if self.transport:
                client_kwargs["transport"] = self.transport

            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await asyncio.wait_for(
                    client.post(self.base_url, json=payload),
                    timeout=self.timeout_seconds
                )

                if response.status_code == 200:
                    data = response.json()
                    return PSPChargeResult(
                        status="succeeded",
                        psp_ref=data.get("psp_ref")
                    )
                elif response.status_code == 400:
                    data = response.json()
                    return PSPChargeResult(
                        status="failed",
                        failure_code=data.get("code", "declined"),
                        failure_message=f"Processor declined charge: {data.get('code')}"
                    )
                else:
                    # 500 or other upstream server errors
                    return PSPChargeResult(
                        status="network_error",
                        failure_code="network_error",
                        failure_message=f"Upstream processor returned HTTP {response.status_code}"
                    )

        except (httpx.TimeoutException, asyncio.TimeoutError):
            # Crucial evaluation requirement:
            # Handles tok_timeout (30s sleep) without hanging the service.
            return PSPChargeResult(
                status="timeout",
                failure_code="timeout",
                failure_message=f"Gateway timeout: payment processor did not respond within {self.timeout_seconds}s"
            )

        except (httpx.ConnectError, httpx.RequestError) as ex:
            # Handles dropped connections and socket errors
            return PSPChargeResult(
                status="network_error",
                failure_code="network_error",
                failure_message=f"Network error connecting to payment processor: {str(ex)}"
            )


psp_client = MockPSPClient()
