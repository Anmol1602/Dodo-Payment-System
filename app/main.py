from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.exceptions import ServiceException
from app.api.v1.router import api_v1_router
from app.mock_psp.routes import router as mock_psp_router
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist in SQLite test/dev environments
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed initial test account
    await seed_database()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Minimal Invoice & Payment Service built with FastAPI, Asynchronous SQLAlchemy, and Mock PSP.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS for local testbeds and tooling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    """Formats custom domain exceptions into consistent error envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Global catch-all for unexpected internal errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal error occurred.",
                "details": {"type": str(type(exc).__name__)}
            }
        }
    )


# Mount API Routers
app.include_router(api_v1_router)
app.include_router(mock_psp_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "dodo-invoice-service",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Dodo Payments Invoice & Payment Service",
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
        "health": "/health",
        "test_api_key": "dodo_live_testkey1234567890abcdef1234567890"
    }
