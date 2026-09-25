from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ScrapeTarget:
    """
    Represents one URL that needs to be scraped.
    """

    url: str
    index: int = 0
    status: str = "queued"

    http_status: int | None = None
    latency_ms: float | None = None

    data: dict[str, Any] | None = None
    error: str | None = None

    worker_id: str | None = None
    proxy_id: str | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class BrowserProfile:
    """
    Browser configuration used by a scraping worker.

    These settings control the browser context rather than attempting
    to bypass security controls.
    """

    viewport_width: int = 1440
    viewport_height: int = 900

    locale: str = "en-US"
    timezone_id: str = "Asia/Kolkata"

    user_agent: str | None = None

    is_mobile: bool = False
    has_touch: bool = False
    device_scale_factor: float = 1.0

    color_scheme: str = "light"


@dataclass
class ProxyConfig:
    """
    Configuration for an authorized proxy endpoint.
    """

    server: str
    username: str | None = None
    password: str | None = None

    def as_playwright_config(self) -> dict[str, str]:
        config: dict[str, str] = {
            "server": self.server,
        }

        if self.username:
            config["username"] = self.username

        if self.password:
            config["password"] = self.password

        return config


@dataclass
class ScrapeResult:
    """
    Result produced by a worker after processing one target.
    """

    url: str
    status: str

    worker_id: str

    http_status: int | None = None
    latency_ms: float | None = None

    data: dict[str, Any] | None = None
    error: str | None = None

    retry_count: int = 0

    blocked: bool = False
    challenge_detected: bool = False

    proxy_id: str | None = None

    created_at: datetime | None = None


@dataclass
class ScrapeJobState:
    """
    In-memory state used by the scraper manager.

    PostgreSQL remains the persistent source of truth.
    """

    job_id: str

    targets: list[ScrapeTarget] = field(
        default_factory=list
    )

    status: str = "queued"

    processed_count: int = 0
    success_count: int = 0
    failed_count: int = 0

    blocked_count: int = 0
    retry_count: int = 0

    started_at: datetime | None = None
    completed_at: datetime | None = None

    errors: list[str] = field(
        default_factory=list
    )

    def mark_processed(
        self,
        result: ScrapeResult,
    ) -> None:
        self.processed_count += 1

        if result.status == "success":
            self.success_count += 1
        else:
            self.failed_count += 1

        if (
            result.blocked
            or result.challenge_detected
        ):
            self.blocked_count += 1

        self.retry_count += result.retry_count

        if result.error:
            self.errors.append(result.error)

        if (
            self.processed_count
            >= len(self.targets)
        ):
            self.status = "completed"