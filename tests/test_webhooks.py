import time
import pytest
from httpx import AsyncClient
from app.core.security import sign_webhook_payload, verify_webhook_signature


@pytest.mark.asyncio
async def test_register_and_list_webhook_endpoints(client: AsyncClient, auth_headers: dict):
    # Register endpoint
    reg_res = await client.post(
        "/api/v1/webhooks/endpoints",
        json={"url": "https://example.com/webhooks"},
        headers=auth_headers
    )
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert data["url"] == "https://example.com/webhooks"
    assert data["secret"].startswith("whsec_")
    assert data["is_active"] is True

    # List endpoints
    list_res = await client.get("/api/v1/webhooks/endpoints", headers=auth_headers)
    assert list_res.status_code == 200
    endpoints = list_res.json()
    assert len(endpoints) >= 1
    assert any(e["id"] == data["id"] for e in endpoints)


def test_webhook_hmac_signature_verification():
    secret = "whsec_test_secret_1234567890"
    payload = b'{"event":"invoice.paid","amount_cents":10500}'
    now = int(time.time())

    # 1. Sign
    header = sign_webhook_payload(secret, payload, now)
    assert header.startswith(f"t={now},v1=")

    # 2. Verify valid
    is_valid = verify_webhook_signature(secret, payload, header, tolerance_seconds=300)
    assert is_valid is True

    # 3. Verify tampering fails
    tampered_payload = b'{"event":"invoice.paid","amount_cents":99999}'
    assert verify_webhook_signature(secret, tampered_payload, header) is False

    # 4. Verify wrong secret fails
    assert verify_webhook_signature("whsec_wrong", payload, header) is False

    # 5. Verify expired timestamp fails (replay attack protection)
    old_timestamp = now - 600  # 10 minutes ago
    old_header = sign_webhook_payload(secret, payload, old_timestamp)
    assert verify_webhook_signature(secret, payload, old_header, tolerance_seconds=300) is False
