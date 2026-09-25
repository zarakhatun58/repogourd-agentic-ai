from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.db.database import SessionLocal
from app.models.scraping import ScrapeJob, ScrapeRecord
from app.services.scraper import (
    BrowserProfile,
    ProxyConfig,
    ScrapeManager,
    ScrapeManagerConfig,
    ScrapeResult,
)


@dataclass
class ScrapeConfig:
    """
    Configuration passed from the API layer to the scraper engine.
    """

    max_concurrency: int = 5
    timeout_ms: int = 15000
    delay_ms: int = 250

    proxy_url: str | None = None
    proxy_username: str | None = None
    proxy_password: str | None = None

    viewport_width: int = 1440
    viewport_height: int = 900
    locale: str = "en-US"
    timezone_id: str = "Asia/Kolkata"

    user_agent: str | None = None
    is_mobile: bool = False
    has_touch: bool = False
    device_scale_factor: float = 1.0
    color_scheme: str = "light"

    max_retries: int = 2
    retry_delay_ms: int = 500
    queue_maxsize: int = 0

    headless: bool = True


def allowed_host(
    url: str,
    allowed_hosts: set[str],
) -> bool:
    """
    Check whether a URL hostname belongs to the configured allowlist.

    The API route performs the primary validation. This second check
    protects background execution from accidentally processing a URL
    outside the authorized target set.
    """
    from urllib.parse import urlparse

    hostname = (urlparse(url).hostname or "").lower()

    return hostname in {
        host.strip().lower()
        for host in allowed_hosts
        if host.strip()
    }


def _update_job(
    job_id: uuid.UUID,
    **values: Any,
) -> None:
    """
    Update a scrape job using a short-lived database session.
    """
    db = SessionLocal()

    try:
        job = db.get(ScrapeJob, job_id)

        if not job:
            return

        for key, value in values.items():
            if hasattr(job, key):
                setattr(job, key, value)

        db.commit()

    finally:
        db.close()


def _append_event(
    job_id: uuid.UUID,
    event_type: str,
    step: int,
    output: dict[str, Any] | None = None,
) -> None:
    """
    Store an observable scraper lifecycle event.

    This intentionally stores operational events only. It does not
    store hidden chain-of-thought or internal reasoning.
    """
    db = SessionLocal()

    try:
        job = db.get(ScrapeJob, job_id)

        if not job:
            return

        profile = dict(job.profile or {})
        events = list(profile.get("events", []))

        events.append(
            {
                "step": step,
                "event_type": event_type,
                "at": datetime.now(timezone.utc).isoformat(),
                "output": output or {},
            }
        )

        profile["events"] = events[-100:]
        job.profile = profile

        db.commit()

    finally:
        db.close()


def _persist_result(
    job_id: uuid.UUID,
    result: ScrapeResult,
) -> None:
    """
    Persist one scraper result into PostgreSQL.
    """
    db = SessionLocal()

    try:
        record = ScrapeRecord(
            job_id=job_id,
            url=result.url,
            status=result.status,
            worker_id=result.worker_id,
            http_status=result.http_status,
            latency_ms=result.latency_ms,
            data=result.data,
            error=result.error,
        )

        db.add(record)
        db.commit()

    finally:
        db.close()


def _build_manager_config(
    config: ScrapeConfig,
) -> ScrapeManagerConfig:
    return ScrapeManagerConfig(
        worker_count=config.max_concurrency,
        max_retries=config.max_retries,
        retry_delay_ms=config.retry_delay_ms,
        navigation_timeout_ms=config.timeout_ms,
        queue_maxsize=config.queue_maxsize,
        viewport_width=config.viewport_width,
        viewport_height=config.viewport_height,
        locale=config.locale,
        timezone_id=config.timezone_id,
        user_agent=config.user_agent,
        is_mobile=config.is_mobile,
        has_touch=config.has_touch,
        device_scale_factor=config.device_scale_factor,
        color_scheme=config.color_scheme,
        proxy_url=config.proxy_url,
        proxy_username=config.proxy_username,
        proxy_password=config.proxy_password,
        headless=config.headless,
    )


def _update_job_counters(
    job_id: uuid.UUID,
    *,
    processed: int,
    success: int,
    failed: int,
    records_per_second: float,
) -> None:
    _update_job(
        job_id,
        processed_count=processed,
        success_count=success,
        failed_count=failed,
        records_per_second=records_per_second,
    )


async def run_scrape_job(
    job_id: uuid.UUID,
    urls: list[str],
    selector_map: dict[str, str],
    config: ScrapeConfig,
) -> None:
    """
    Run a complete scraper job in the background.

    Flow:

        ScrapeJob
            ↓
        ScrapeManager
            ↓
        Queue
            ↓
        Worker Pool
            ↓
        Playwright
            ↓
        Extractor
            ↓
        PostgreSQL ScrapeRecord
    """

    started_at = datetime.now(timezone.utc)

    _update_job(
        job_id,
        status="running",
        started_at=started_at,
        error_message=None,
    )

    _append_event(
        job_id,
        "scraping_job_started",
        1,
        {
            "target_count": len(urls),
            "concurrency": config.max_concurrency,
        },
    )

    _append_event(
        job_id,
        "scraper_engine_initializing",
        2,
        {
            "playwright": True,
            "headless": config.headless,
            "proxy_configured": bool(config.proxy_url),
        },
    )

    persisted_count = 0
    success_count = 0
    failed_count = 0

    async def on_result(result: ScrapeResult) -> None:
        nonlocal persisted_count
        nonlocal success_count
        nonlocal failed_count

        _persist_result(
            job_id,
            result,
        )

        persisted_count += 1

        if result.status == "success":
            success_count += 1
        else:
            failed_count += 1

        elapsed = max(
            (
                datetime.now(timezone.utc)
                - started_at
            ).total_seconds(),
            0.001,
        )

        records_per_second = round(
            persisted_count / elapsed,
            2,
        )

        _update_job_counters(
            job_id,
            processed=persisted_count,
            success=success_count,
            failed=failed_count,
            records_per_second=records_per_second,
        )

    manager = ScrapeManager(
        config=_build_manager_config(config),
        selector_map=selector_map,
        on_result=on_result,
    )

    try:
        _append_event(
            job_id,
            "browser_initialization_started",
            3,
            {
                "worker_count": config.max_concurrency,
            },
        )

        run = await manager.run(
            urls,
            run_id=str(job_id),
        )

        _append_event(
            job_id,
            "records_persisted",
            4,
            {
                "processed": persisted_count,
                "success": success_count,
                "failed": failed_count,
            },
        )

        metrics = manager.metrics.snapshot()

        completed_at = datetime.now(timezone.utc)

        _update_job(
            job_id,
            status="completed",
            completed_at=completed_at,
            processed_count=persisted_count,
            success_count=success_count,
            failed_count=failed_count,
            records_per_second=metrics["records_per_second"],
        )

        _append_event(
            job_id,
            "scraping_job_completed",
            5,
            {
                "status": run.status,
                "processed": persisted_count,
                "success": success_count,
                "failed": failed_count,
                "records_per_second": metrics[
                    "records_per_second"
                ],
                "average_latency_ms": metrics[
                    "average_latency_ms"
                ],
                "p50_latency_ms": metrics[
                    "p50_latency_ms"
                ],
                "p95_latency_ms": metrics[
                    "p95_latency_ms"
                ],
                "p99_latency_ms": metrics[
                    "p99_latency_ms"
                ],
                "retry_count": metrics[
                    "retry_count"
                ],
                "timeout_count": metrics[
                    "timeout_count"
                ],
                "blocked_count": metrics[
                    "blocked_count"
                ],
            },
        )

    except asyncio.CancelledError:
        _update_job(
            job_id,
            status="cancelled",
            completed_at=datetime.now(timezone.utc),
            processed_count=persisted_count,
            success_count=success_count,
            failed_count=failed_count,
        )

        _append_event(
            job_id,
            "scraping_job_cancelled",
            5,
            {
                "processed": persisted_count,
            },
        )

        raise

    except Exception as exc:
        error_message = str(exc)[:2000]

        _update_job(
            job_id,
            status="failed",
            completed_at=datetime.now(timezone.utc),
            processed_count=persisted_count,
            success_count=success_count,
            failed_count=failed_count,
            error_message=error_message,
        )

        _append_event(
            job_id,
            "scraping_job_failed",
            5,
            {
                "error": error_message,
                "processed": persisted_count,
            },
        )

    finally:
        await manager.shutdown()


def start_scrape_job(
    job_id: uuid.UUID,
    urls: list[str],
    selector_map: dict[str, str],
    config: ScrapeConfig,
):
    """
    Compatibility helper for callers that prefer creating an asyncio task.
    """
    return asyncio.create_task(
        run_scrape_job(
            job_id,
            urls,
            selector_map,
            config,
        )
    )