from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import generate_webhook_secret
from app.core.exceptions import ResourceNotFoundError
from app.models.business import Business
from app.models.webhook import WebhookEndpoint, WebhookDelivery
from app.schemas.webhook import (
    WebhookEndpointCreateRequest,
    WebhookEndpointResponse,
    WebhookDeliveryResponse,
)
from app.api.deps import get_current_business

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/endpoints", response_model=WebhookEndpointResponse, status_code=status.HTTP_201_CREATED)
async def register_webhook_endpoint(
    payload: WebhookEndpointCreateRequest,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """
    Registers an HTTPS webhook endpoint for the business.
    Generates a secret used to sign HMAC-SHA256 headers.
    """
    secret = generate_webhook_secret()
    endpoint = WebhookEndpoint(
        business_id=business.id,
        url=str(payload.url),
        secret=secret,
        is_active=True,
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    return endpoint


@router.get("/endpoints", response_model=List[WebhookEndpointResponse])
async def list_webhook_endpoints(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Lists all registered webhook endpoints for the authenticated business."""
    query = (
        select(WebhookEndpoint)
        .where(WebhookEndpoint.business_id == business.id)
        .order_by(WebhookEndpoint.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.delete("/endpoints/{endpoint_id}", status_code=status.HTTP_200_OK)
async def delete_webhook_endpoint(
    endpoint_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Deletes or disables a webhook endpoint."""
    query = select(WebhookEndpoint).where(
        WebhookEndpoint.id == endpoint_id,
        WebhookEndpoint.business_id == business.id
    )
    result = await db.execute(query)
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise ResourceNotFoundError("WebhookEndpoint", endpoint_id)

    endpoint.is_active = False
    await db.commit()
    return {"message": "Webhook endpoint deactivated successfully", "id": endpoint_id}


@router.get("/deliveries", response_model=List[WebhookDeliveryResponse])
async def list_webhook_deliveries(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Lists recent webhook delivery logs for auditability."""
    query = (
        select(WebhookDelivery)
        .join(WebhookEndpoint, WebhookDelivery.endpoint_id == WebhookEndpoint.id)
        .where(WebhookEndpoint.business_id == business.id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
