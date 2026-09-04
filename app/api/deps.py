from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import hash_api_key, verify_api_key
from app.core.exceptions import AuthenticationError
from app.models.business import Business, ApiKey


async def get_current_business(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> Business:
    """
    Extracts API key from either:
      - Authorization: Bearer <key>
      - X-API-Key: <key>
    Verifies key against active API keys in database using SHA-256 hash.
    """
    raw_key: Optional[str] = None

    if authorization and authorization.startswith("Bearer "):
        raw_key = authorization[7:].strip()
    elif x_api_key:
        raw_key = x_api_key.strip()

    if not raw_key:
        raise AuthenticationError("API key required. Provide via 'Authorization: Bearer <key>' or 'X-API-Key'.")

    # Compute SHA-256 hash
    key_hash = hash_api_key(raw_key)

    query = select(ApiKey).where(
        ApiKey.key_hash == key_hash,
        ApiKey.is_revoked == False
    )
    result = await db.execute(query)
    api_key_record = result.scalar_one_or_none()

    if not api_key_record:
        raise AuthenticationError("Invalid or revoked API key.")

    business = await db.get(Business, api_key_record.business_id)
    if not business:
        raise AuthenticationError("Associated business account not found.")

    return business
