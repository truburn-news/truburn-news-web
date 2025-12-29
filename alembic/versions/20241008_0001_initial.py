"""initial schema for Truburn Phase1

Revision ID: 20241008_0001
Revises: 
Create Date: 2024-10-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20241008_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use non-native enums to avoid global TYPE conflicts; CHECK constraints are created instead.
    record_status_col = sa.Enum(
        "live", "under_review", "verified", "falsified", name="recordstatus", native_enum=False
    )
    review_status_col = sa.Enum("open", "finalized", name="reviewrequeststatus", native_enum=False)
    review_verdict_col = sa.Enum("verified", "falsified", name="reviewverdict", native_enum=False)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("wallet_address", sa.String(length=120), nullable=False, unique=True),
        sa.Column("vp_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("time_occurred_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_occurred_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolution_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("resolution_multiplier", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("status", record_status_col, nullable=False, server_default="live"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "review_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records.id", ondelete="CASCADE")),
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_url", sa.String(length=500), nullable=False),
        sa.Column("is_counter_evidence", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", review_status_col, nullable=False, server_default="open"),
        sa.Column("verdict", review_verdict_col, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vp_cost", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "verification_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records.id", ondelete="SET NULL")),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("verification_points")
    op.drop_table("review_requests")
    op.drop_table("records")
    op.drop_table("users")
    sa.Enum(name="reviewverdict").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reviewrequeststatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="recordstatus").drop(op.get_bind(), checkfirst=True)
