from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.customers import router as customers_router
from app.api.v1.invoices import router as invoices_router
from app.api.v1.payments import router as payments_router
from app.api.v1.webhooks import router as webhooks_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(customers_router)
api_v1_router.include_router(invoices_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(webhooks_router)
