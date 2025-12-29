from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import RecordStatus, ReviewRequest, ReviewRequestStatus, ReviewVerdict


async def finalize_expired_reviews(session: AsyncSession, now: datetime | None = None) -> int:
    """
    Batch finalize review requests that reached expires_at.
    Returns the number of finalized requests.
    """
    now = now or datetime.now(timezone.utc)
    result = await session.execute(
        select(ReviewRequest)
        .where(ReviewRequest.status == ReviewRequestStatus.open)
        .where(ReviewRequest.expires_at <= now)
        .order_by(ReviewRequest.expires_at)
    )
    requests = result.scalars().all()
    finalized = 0
    for rr in requests:
        verdict = ReviewVerdict.falsified if rr.is_counter_evidence else ReviewVerdict.verified
        rr.status = ReviewRequestStatus.finalized
        rr.verdict = verdict
        rr.finalized_at = now
        if verdict == ReviewVerdict.falsified:
            rr.record.status = RecordStatus.falsified
        elif rr.record.status != RecordStatus.falsified:
            rr.record.status = RecordStatus.verified
        finalized += 1
    if finalized:
        await session.commit()
    return finalized
