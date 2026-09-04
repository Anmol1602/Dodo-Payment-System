from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.models.business import Business
from app.models.customer import Customer
from app.schemas.customer import CustomerCreateRequest, CustomerResponse
from app.api.deps import get_current_business

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreateRequest,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Creates a customer scoped to the authenticated business."""
    customer = Customer(
        business_id=business.id,
        name=payload.name.strip(),
        email=payload.email.strip().lower(),
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Lists customers scoped to the authenticated business."""
    query = (
        select(Customer)
        .where(Customer.business_id == business.id)
        .order_by(Customer.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single customer by ID (scoped to authenticated business)."""
    query = select(Customer).where(
        Customer.id == customer_id,
        Customer.business_id == business.id
    )
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    if not customer:
        raise ResourceNotFoundError("Customer", customer_id)
    return customer
