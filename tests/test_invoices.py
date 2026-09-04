import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_invoice_computes_total_in_cents(client: AsyncClient, auth_headers: dict):
    # 1. Get seeded customer
    cust_res = await client.get("/api/v1/customers", headers=auth_headers)
    customer_id = cust_res.json()[0]["id"]

    # 2. Create invoice with 2 items: 2 * 4500 cents ($45.00) + 1 * 1500 cents ($15.00)
    # Expected server calculated total = 9000 + 1500 = 10500 cents ($105.00)
    invoice_payload = {
        "customer_id": customer_id,
        "due_date": "2026-09-30",
        "auto_finalize": True,
        "line_items": [
            {
                "description": "Enterprise Cloud Server",
                "quantity": 2,
                "unit_amount_cents": 4500
            },
            {
                "description": "Static IP",
                "quantity": 1,
                "unit_amount_cents": 1500
            }
        ]
    }
    response = await client.post("/api/v1/invoices", json=invoice_payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["total_amount_cents"] == 10500
    assert data["state"] == "open"
    assert data["currency"] == "USD"
    assert len(data["line_items"]) == 2
    assert data["line_items"][0]["total_amount_cents"] == 9000
    assert data["line_items"][1]["total_amount_cents"] == 1500


@pytest.mark.asyncio
async def test_create_invoice_draft_and_finalize(client: AsyncClient, auth_headers: dict):
    cust_res = await client.get("/api/v1/customers", headers=auth_headers)
    customer_id = cust_res.json()[0]["id"]

    invoice_payload = {
        "customer_id": customer_id,
        "due_date": "2026-10-15",
        "auto_finalize": False,  # Should start as draft
        "line_items": [
            {"description": "Consulting Hour", "quantity": 5, "unit_amount_cents": 10000}
        ]
    }
    create_res = await client.post("/api/v1/invoices", json=invoice_payload, headers=auth_headers)
    assert create_res.status_code == 201
    inv_id = create_res.json()["id"]
    assert create_res.json()["state"] == "draft"

    # Finalize draft -> open
    fin_res = await client.post(f"/api/v1/invoices/{inv_id}/finalize", headers=auth_headers)
    assert fin_res.status_code == 200
    assert fin_res.json()["state"] == "open"


@pytest.mark.asyncio
async def test_filter_invoices_by_state(client: AsyncClient, auth_headers: dict):
    # Fetch invoices with state=open
    res = await client.get("/api/v1/invoices?state=open", headers=auth_headers)
    assert res.status_code == 200
    invoices = res.json()
    assert isinstance(invoices, list)
    for inv in invoices:
        assert inv["state"] == "open"
