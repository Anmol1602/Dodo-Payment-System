import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# Handle driver prefixes properly
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# SQLite fallback support for running unit tests without external Postgres
is_sqlite = DATABASE_URL.startswith("sqlite")

engine_kwargs = {
    "echo": False,
    "future": True,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
    })

engine = create_async_engine(DATABASE_URL, **engine_kwargs)
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
