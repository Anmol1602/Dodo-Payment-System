from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import generate_api_key
from app.core.exceptions import ResourceNotFoundError
from app.models.business import Business, ApiKey
from app.schemas.business import (
    BusinessRegisterRequest,
    BusinessRegisterResponse,
    ApiKeyCreateRequest,
    ApiKeyResponse,
)
from app.api.deps import get_current_business

router = APIRouter(prefix="/auth", tags=["Authentication & Businesses"])


@router.post("/register", response_model=BusinessRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_business(payload: BusinessRegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Onboards a new business and returns an initial API key.
    The raw API key is returned exactly once.
    """
    business = Business(name=payload.name)
    db.add(business)
    await db.flush()

    raw_key, prefix, key_hash = generate_api_key(is_test=False)
    api_key = ApiKey(
        business_id=business.id,
        key_prefix=prefix,
        key_hash=key_hash,
        label="Initial Primary Key",
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(business)

    return BusinessRegisterResponse(
        business_id=business.id,
        name=business.name,
        api_key=raw_key,
        created_at=business.created_at,
    )


@router.post("/api-keys", response_model=BusinessRegisterResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Generates an additional API key for the authenticated business."""
    raw_key, prefix, key_hash = generate_api_key(is_test=payload.is_test)
    api_key = ApiKey(
        business_id=business.id,
        key_prefix=prefix,
        key_hash=key_hash,
        label=payload.label,
    )
    db.add(api_key)
    await db.commit()

    return BusinessRegisterResponse(
        business_id=business.id,
        name=business.name,
        api_key=raw_key,
        created_at=api_key.created_at,
    )


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Lists all API keys for the authenticated business (hashes are never returned)."""
    query = select(ApiKey).where(ApiKey.business_id == business.id).order_by(ApiKey.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/api-keys/{key_id}/revoke", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    key_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Instantly revokes an API key."""
    query = select(ApiKey).where(ApiKey.id == key_id, ApiKey.business_id == business.id)
    result = await db.execute(query)
    key_record = result.scalar_one_or_none()
    if not key_record:
        raise ResourceNotFoundError("ApiKey", key_id)

    key_record.is_revoked = True
    key_record.revoked_at = datetime.utcnow()
    await db.commit()

    return {"message": "API key revoked successfully", "id": key_id}
