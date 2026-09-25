from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class ScrapeJobCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    urls: list[HttpUrl] = Field(min_length=1, max_length=100)
    selector_map: dict[str, str] = Field(default_factory=dict)
    max_concurrency: int = Field(default=5, ge=1, le=20)
    delay_ms: int = Field(default=250, ge=0, le=10000)
    timeout_ms: int = Field(default=15000, ge=1000, le=60000)
    proxy_url: str | None = None
    viewport_width: int = Field(default=1440, ge=320, le=3000)
    viewport_height: int = Field(default=900, ge=240, le=3000)
    locale: str = "en-US"
    timezone_id: str = "Asia/Kolkata"


class ScrapeJobResponse(BaseModel):
    id: UUID
    name: str
    status: str
    target_count: int
    max_concurrency: int
    proxy_configured: bool
    processed_count: int
    success_count: int
    failed_count: int
    records_per_second: float
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    class Config:
        from_attributes = True


class ScrapeRecordResponse(BaseModel):
    id: UUID
    url: str
    status: str
    worker_id: str
    http_status: int | None
    latency_ms: float | None
    data: dict | None
    error: str | None
    created_at: datetime

    class Config:
        from_attributes = True
