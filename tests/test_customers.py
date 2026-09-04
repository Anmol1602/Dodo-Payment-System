import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_customer_success(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/customers",
        json={"name": "Alice Smith", "email": "alice@smith.org"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice Smith"
    assert data["email"] == "alice@smith.org"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_customer_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/customers",
        json={"name": "No Auth", "email": "noauth@test.com"},
        headers={"Authorization": "Bearer invalid_key"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_list_customers(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/customers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
