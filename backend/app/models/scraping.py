import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, Float, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued", index=True)
    target_count: Mapped[int] = mapped_column(Integer, nullable=False)
    max_concurrency: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    proxy_configured: Mapped[bool] = mapped_column(nullable=False, default=False)
    profile: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    selector_map: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_per_second: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ScrapeRecord(Base):
    __tablename__ = "scrape_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scrape_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    worker_id: Mapped[str] = mapped_column(String(100), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
