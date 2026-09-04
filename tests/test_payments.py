import pytest
from httpx import AsyncClient


async def _create_test_invoice(client: AsyncClient, auth_headers: dict) -> str:
    cust_res = await client.get("/api/v1/customers", headers=auth_headers)
    customer_id = cust_res.json()[0]["id"]
    invoice_payload = {
        "customer_id": customer_id,
        "due_date": "2026-09-30",
        "auto_finalize": True,
        "line_items": [
            {"description": "Web Hosting", "quantity": 1, "unit_amount_cents": 5000}
        ]
    }
    res = await client.post("/api/v1/invoices", json=invoice_payload, headers=auth_headers)
    return res.json()["id"]


@pytest.mark.asyncio
async def test_pay_success_transitions_to_paid(client: AsyncClient, auth_headers: dict):
    invoice_id = await _create_test_invoice(client, auth_headers)

    headers = {**auth_headers, "Idempotency-Key": "test_pay_succ_001"}
    pay_res = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_success"},
        headers=headers
    )
    assert pay_res.status_code == 200
    data = pay_res.json()
    assert data["status"] == "succeeded"
    assert data["invoice_state"] == "paid"
    assert "psp_reference" in data

    # Verify invoice state via GET
    inv_res = await client.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
    assert inv_res.json()["state"] == "paid"

    # Attempting to pay an already paid invoice must be rejected
    fail_res = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_success"},
        headers={**auth_headers, "Idempotency-Key": "new_key_different"}
    )
    assert fail_res.status_code == 409
    assert fail_res.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


@pytest.mark.asyncio
async def test_pay_insufficient_funds_leaves_invoice_open(client: AsyncClient, auth_headers: dict):
    invoice_id = await _create_test_invoice(client, auth_headers)

    headers = {**auth_headers, "Idempotency-Key": "test_pay_funds_001"}
    pay_res = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_insufficient_funds"},
        headers=headers
    )
    assert pay_res.status_code == 402
    err = pay_res.json()["error"]
    assert err["code"] == "PAYMENT_FAILED"
    assert err["details"]["failure_code"] == "insufficient_funds"

    # Invoice must remain OPEN so customer can retry
    inv_res = await client.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
    assert inv_res.json()["state"] == "open"


@pytest.mark.asyncio
async def test_pay_card_declined(client: AsyncClient, auth_headers: dict):
    invoice_id = await _create_test_invoice(client, auth_headers)

    headers = {**auth_headers, "Idempotency-Key": "test_pay_decline_001"}
    pay_res = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_card_declined"},
        headers=headers
    )
    assert pay_res.status_code == 402
    err = pay_res.json()["error"]
    assert err["details"]["failure_code"] == "card_declined"


@pytest.mark.asyncio
async def test_pay_timeout_handled_gracefully(client: AsyncClient, auth_headers: dict, monkeypatch):
    """
    Simulates tok_timeout by configuring short timeout on psp_client.
    Verifies that the server does NOT hang and invoice state remains uncorrupted.
    """
    invoice_id = await _create_test_invoice(client, auth_headers)

    headers = {**auth_headers, "Idempotency-Key": "test_pay_timeout_001"}
    pay_res = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_timeout"},
        headers=headers
    )
    # The client timeout catches tok_timeout and returns 504
    assert pay_res.status_code == 504
    err = pay_res.json()["error"]
    assert err["code"] == "PSP_TIMEOUT"

    # Invoice state must remain safely OPEN
    inv_res = await client.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
    assert inv_res.json()["state"] == "open"


@pytest.mark.asyncio
async def test_pay_network_error_handled(client: AsyncClient, auth_headers: dict):
    invoice_id = await _create_test_invoice(client, auth_headers)

    headers = {**auth_headers, "Idempotency-Key": "test_pay_neterr_001"}
    pay_res = await client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        json={"card_token": "tok_network_error"},
        headers=headers
    )
    assert pay_res.status_code == 502
    err = pay_res.json()["error"]
    assert err["code"] == "PSP_NETWORK_ERROR"

    # Invoice remains safely OPEN
    inv_res = await client.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
    assert inv_res.json()["state"] == "open"
