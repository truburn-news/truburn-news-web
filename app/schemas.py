import uuid
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

from .models import ReviewStatus


class RecordCreate(BaseModel):
    title: str = Field(..., max_length=200)
    body: str
    source_url: Optional[HttpUrl] = None
    time_occurred_start: Optional[datetime] = None
    time_occurred_end: Optional[datetime] = None


class RecordRead(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    source_url: Optional[str] = None
    time_occurred_start: Optional[datetime] = None
    time_occurred_end: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewRequestCreate(BaseModel):
    record_id: uuid.UUID


class ReviewRequestRead(BaseModel):
    id: uuid.UUID
    record_id: uuid.UUID
    status: ReviewStatus
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
