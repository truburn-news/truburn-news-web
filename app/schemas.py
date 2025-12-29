import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from .models import RecordStatus, ReviewRequestStatus, ReviewVerdict


class RecordCreate(BaseModel):
    title: str = Field(..., max_length=200)
    body: str
    evidence_url: Optional[HttpUrl] = None
    time_occurred_start: datetime
    time_occurred_end: datetime


class RecordRead(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    evidence_url: Optional[str] = None
    time_occurred_start: datetime
    time_occurred_end: datetime
    resolution_level: int
    resolution_multiplier: float
    status: RecordStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewRequestCreate(BaseModel):
    record_id: uuid.UUID
    reason: str = Field(..., min_length=200)
    evidence_url: HttpUrl
    is_counter_evidence: bool = True


class ReviewRequestRead(BaseModel):
    id: uuid.UUID
    record_id: uuid.UUID
    requester_id: Optional[uuid.UUID] = None
    reason: str
    evidence_url: str
    is_counter_evidence: bool
    status: ReviewRequestStatus
    verdict: Optional[ReviewVerdict] = None
    expires_at: datetime
    finalized_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
