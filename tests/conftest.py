import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["PSP_TIMEOUT_SECONDS"] = "1.0"

from app.core.database import Base, get_db
from app.core.security import hash_api_key
from app.models.business import Business, ApiKey
from app.models.customer import Customer
from app.main import app

TEST_API_KEY = "dodo_test_validkey1234567890abcdef1234567890"

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        # Seed test business
        business = Business(name="Test Business Corp")
        session.add(business)
        await session.flush()

        api_key = ApiKey(
            business_id=business.id,
            key_prefix="dodo_test_",
            key_hash=hash_api_key(TEST_API_KEY),
            label="Test Key",
        )
        session.add(api_key)

        customer = Customer(
            business_id=business.id,
            name="John Doe",
            email="john@example.com"
        )
        session.add(customer)
        await session.commit()

        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


from app.services.psp_client import psp_client

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    old_transport = psp_client.transport
    old_base_url = psp_client.base_url
    old_timeout = psp_client.timeout_seconds

    psp_client.transport = transport
    psp_client.base_url = "http://test/mock-psp/charge"
    psp_client.timeout_seconds = 1.0

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    psp_client.transport = old_transport
    psp_client.base_url = old_base_url
    psp_client.timeout_seconds = old_timeout
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    return {
        "Authorization": f"Bearer {TEST_API_KEY}",
        "Content-Type": "application/json"
    }
