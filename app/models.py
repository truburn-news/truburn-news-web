from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RecordStatus(StrEnum):
    live = "live"
    under_review = "under_review"
    verified = "verified"
    falsified = "falsified"


class ReviewRequestStatus(StrEnum):
    open = "open"
    finalized = "finalized"


class ReviewVerdict(StrEnum):
    verified = "verified"
    falsified = "falsified"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    vp_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    records: Mapped[list["Record"]] = relationship(back_populates="author")
    review_requests: Mapped[list["ReviewRequest"]] = relationship(back_populates="requester")
    vp_transactions: Mapped[list["VerificationPoint"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Record(Base):
    __tablename__ = "records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    time_occurred_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_occurred_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolution_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    resolution_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, native_enum=False, name="recordstatus"),
        nullable=False,
        default=RecordStatus.live,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    review_requests: Mapped[list["ReviewRequest"]] = relationship(
        back_populates="record", cascade="all, delete-orphan"
    )
    author: Mapped[User | None] = relationship(back_populates="records")


class ReviewRequest(Base):
    __tablename__ = "review_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("records.id", ondelete="CASCADE"))
    requester_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_counter_evidence: Mapped[bool] = mapped_column(default=True, nullable=False)
    status: Mapped[ReviewRequestStatus] = mapped_column(
        Enum(ReviewRequestStatus, native_enum=False, name="reviewrequeststatus"),
        nullable=False,
        default=ReviewRequestStatus.open,
    )
    verdict: Mapped[ReviewVerdict | None] = mapped_column(
        Enum(ReviewVerdict, native_enum=False, name="reviewverdict"), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vp_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    record: Mapped["Record"] = relationship(back_populates="review_requests")
    requester: Mapped[User | None] = relationship(back_populates="review_requests")


class VerificationPoint(Base):
    """
    VP transaction log (positive or negative).
    """

    __tablename__ = "verification_points"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    record_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("records.id", ondelete="SET NULL"))
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="vp_transactions")
    record: Mapped[Record | None] = relationship()
