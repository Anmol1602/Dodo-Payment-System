import asyncio
import logging
from sqlalchemy import select
from app.core.database import async_session_factory
from app.core.security import hash_api_key
from app.models.business import Business, ApiKey
from app.models.customer import Customer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

DEFAULT_TEST_KEY = "dodo_live_testkey1234567890abcdef1234567890"


async def seed_database():
    """
    Seeds an initial business and standard test API key so curl commands
    work immediately upon 'docker compose up'.
    """
    async with async_session_factory() as session:
        try:
            key_hash = hash_api_key(DEFAULT_TEST_KEY)
            query = select(ApiKey).where(ApiKey.key_hash == key_hash)
            result = await session.execute(query)
            existing_key = result.scalar_one_or_none()

            if not existing_key:
                logger.info("Seeding initial business and test API key...")
                business = Business(name="Acme Cloud Inc.")
                session.add(business)
                await session.flush()

                api_key = ApiKey(
                    business_id=business.id,
                    key_prefix="dodo_live_",
                    key_hash=key_hash,
                    label="Primary Development Key"
                )
                session.add(api_key)

                # Seed sample customer
                customer = Customer(
                    business_id=business.id,
                    name="Sarah Connor",
                    email="sarah@cyberdyne.com"
                )
                session.add(customer)

                await session.commit()
                logger.info(f"Database seeded successfully. Test API Key: {DEFAULT_TEST_KEY}")
            else:
                logger.info("Database already seeded. Skipping.")
        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(seed_database())
