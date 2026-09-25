"""add web automation scraping jobs and records

Revision ID: f31c9a7b1e22
Revises: 96df5295f2cb
Create Date: 2026-09-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f31c9a7b1e22"
down_revision: Union[str, None] = "96df5295f2cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scrape_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("target_count", sa.Integer(), nullable=False),
        sa.Column("max_concurrency", sa.Integer(), nullable=False),
        sa.Column("proxy_configured", sa.Boolean(), nullable=False),
        sa.Column("profile", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("selector_map", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_count", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("records_per_second", sa.Float(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrape_jobs_status", "scrape_jobs", ["status"])

    op.create_table(
        "scrape_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("worker_id", sa.String(length=100), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["scrape_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrape_records_job_id", "scrape_records", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_scrape_records_job_id", table_name="scrape_records")
    op.drop_table("scrape_records")
    op.drop_index("ix_scrape_jobs_status", table_name="scrape_jobs")
    op.drop_table("scrape_jobs")
