import asyncio
from datetime import datetime, timezone

from ..database import AsyncSessionLocal
from ..services.review import finalize_expired_reviews


async def run():
    async with AsyncSessionLocal() as session:
        count = await finalize_expired_reviews(session, now=datetime.now(timezone.utc))
        print(f"Finalized {count} review requests.")


if __name__ == "__main__":
    asyncio.run(run())
