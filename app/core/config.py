import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Dodo Invoicing & Payment Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database: Async Postgres by default, fallbacks to local sqlite for tests/dev
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/dodo_invoices"
    )

    # PSP Configuration
    # Defaults to local route or standalone mock-psp container
    PSP_URL: str = os.getenv("PSP_URL", "http://localhost:8000/mock-psp/charge")
    PSP_TIMEOUT_SECONDS: float = float(os.getenv("PSP_TIMEOUT_SECONDS", "5.0"))

    # Webhook Retry Configuration
    WEBHOOK_MAX_RETRIES: int = 5
    WEBHOOK_TIMEOUT_SECONDS: float = 5.0
    WEBHOOK_BASE_BACKOFF_SECONDS: float = 15.0

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
