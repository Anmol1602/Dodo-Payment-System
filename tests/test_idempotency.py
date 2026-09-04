import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_idempotency_cached_replay(client: AsyncClient, auth_headers: dict):
    cust_res = await client.get("/api/v1/customers", headers=auth_headers)
    customer_id = cust_res.json()[0]["id"]
    invoice_payload = {
        "customer_id": customer_id,
        "due_date": "2026-09-30",
        "auto_finalize": True,
        "line_items": [{"description": "SaaS License", "quantity": 1, "unit_amount_cents": 2900}]
    }
    inv_res = await client.post("/api/v1/invoices", json=invoice_payload, headers=auth_headers)
    invoice_id = inv_res.json()["id"]

    idemp_key = "idemp_unique_key_abc_123"
    headers = {**auth_headers, "Idempotency-Key": idemp_key}

    # First request: process payment
    res1 = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_success"},
        headers=headers
    )
    assert res1.status_code == 200
    data1 = res1.json()

    # Second request: identical key and payload -> must return exact cached response
    res2 = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_success"},
        headers=headers
    )
    assert res2.status_code == 200
    data2 = res2.json()

    assert data1["payment_attempt_id"] == data2["payment_attempt_id"]
    assert data1["psp_reference"] == data2["psp_reference"]


@pytest.mark.asyncio
async def test_idempotency_mismatched_payload_rejected(client: AsyncClient, auth_headers: dict):
    cust_res = await client.get("/api/v1/customers", headers=auth_headers)
    customer_id = cust_res.json()[0]["id"]
    invoice_payload = {
        "customer_id": customer_id,
        "due_date": "2026-09-30",
        "auto_finalize": True,
        "line_items": [{"description": "Setup Fee", "quantity": 1, "unit_amount_cents": 1000}]
    }
    inv_res = await client.post("/api/v1/invoices", json=invoice_payload, headers=auth_headers)
    invoice_id = inv_res.json()["id"]

    idemp_key = "idemp_conflict_key_999"
    headers = {**auth_headers, "Idempotency-Key": idemp_key}

    # First request with tok_insufficient_funds
    res1 = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_insufficient_funds"},
        headers=headers
    )
    assert res1.status_code == 402

    # Second request with SAME key but DIFFERENT payload (tok_success) -> must reject with 422
    res2 = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_success"},
        headers=headers
    )
    assert res2.status_code == 422
    assert res2.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


@pytest.mark.asyncio
async def test_missing_idempotency_key_header_rejected(client: AsyncClient, auth_headers: dict):
    cust_res = await client.get("/api/v1/customers", headers=auth_headers)
    customer_id = cust_res.json()[0]["id"]
    inv_res = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "due_date": "2026-09-30",
            "auto_finalize": True,
            "line_items": [{"description": "Item", "quantity": 1, "unit_amount_cents": 500}]
        },
        headers=auth_headers
    )
    invoice_id = inv_res.json()["id"]

    # Post without Idempotency-Key
    res = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_success"},
        headers=auth_headers
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"
