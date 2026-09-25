import asyncio
import os
from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.scraping import ScrapeJob, ScrapeRecord
from app.schemas.scraping import (
    ScrapeJobCreate,
    ScrapeJobResponse,
    ScrapeRecordResponse,
)
from app.services.scraper_service import ScrapeConfig, run_scrape_job


router = APIRouter(
    prefix="/scraping",
    tags=["Web Automation"],
)


def _allowed_hosts() -> set[str]:
    raw = os.getenv(
        "SCRAPER_ALLOWED_HOSTS",
        "localhost,127.0.0.1",
    )

    return {
        value.strip().lower()
        for value in raw.split(",")
        if value.strip()
    }


def _validate_target_urls(urls: list[str]) -> None:
    allowed = _allowed_hosts()

    for url in urls:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        if parsed.scheme not in {"http", "https"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported URL scheme for target: {url}",
            )

        if hostname not in allowed:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Target host is not in SCRAPER_ALLOWED_HOSTS. "
                    "Configure only targets you are authorized to automate."
                ),
            )


@router.post(
    "/jobs",
    response_model=ScrapeJobResponse,
    status_code=202,
)
async def create_scrape_job(
    payload: ScrapeJobCreate,
    db: Session = Depends(get_db),
):
    urls = [str(url) for url in payload.urls]

    _validate_target_urls(urls)

    job = ScrapeJob(
        name=payload.name,
        status="queued",
        target_count=len(urls),
        max_concurrency=payload.max_concurrency,
        proxy_configured=bool(payload.proxy_url),
        profile={
            "viewport_width": payload.viewport_width,
            "viewport_height": payload.viewport_height,
            "locale": payload.locale,
            "timezone_id": payload.timezone_id,
            "events": [],
        },
        selector_map=payload.selector_map,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    config = ScrapeConfig(
        max_concurrency=payload.max_concurrency,
        timeout_ms=payload.timeout_ms,
        delay_ms=payload.delay_ms,
        proxy_url=payload.proxy_url,
        viewport_width=payload.viewport_width,
        viewport_height=payload.viewport_height,
        locale=payload.locale,
        timezone_id=payload.timezone_id,
        max_retries=2,
        retry_delay_ms=max(payload.delay_ms, 250),
        headless=True,
    )

    asyncio.create_task(
        run_scrape_job(
            job.id,
            urls,
            payload.selector_map,
            config,
        )
    )

    return job


@router.get(
    "/jobs",
    response_model=list[ScrapeJobResponse],
)
def list_scrape_jobs(
    db: Session = Depends(get_db),
):
    return (
        db.query(ScrapeJob)
        .order_by(ScrapeJob.created_at.desc())
        .limit(100)
        .all()
    )


@router.get(
    "/jobs/{job_id}",
    response_model=ScrapeJobResponse,
)
def get_scrape_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = db.get(ScrapeJob, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Scrape job not found",
        )

    return job


@router.get(
    "/jobs/{job_id}/records",
    response_model=list[ScrapeRecordResponse],
)
def get_scrape_records(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    if not db.get(ScrapeJob, job_id):
        raise HTTPException(
            status_code=404,
            detail="Scrape job not found",
        )

    return (
        db.query(ScrapeRecord)
        .filter(ScrapeRecord.job_id == job_id)
        .order_by(ScrapeRecord.created_at.asc())
        .limit(1000)
        .all()
    )


@router.get("/jobs/{job_id}/events")
def get_scrape_events(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = db.get(ScrapeJob, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Scrape job not found",
        )

    return {
        "job_id": str(job.id),
        "events": (job.profile or {}).get("events", []),
    }