import asyncio
import uuid

from app.services.scraper_service import ScrapeConfig
from app.services.scraper_service import run_scrape_job


async def main():
    job_id = uuid.uuid4()

    urls = [
        "http://127.0.0.1:8100/item/1",
        "http://127.0.0.1:8100/item/2",
        "http://127.0.0.1:8100/item/3",
    ]

    selector_map = {
        "title": ".item-title",
        "description": ".item-description",
        "price": ".price",
        "category": ".category",
        "item_id": ".item-id",
    }

    config = ScrapeConfig(
        max_concurrency=3,
        timeout_ms=15000,
        delay_ms=250,
        max_retries=1,
        retry_delay_ms=250,
        headless=True,
    )

    print("Starting scraper service test...")
    print("Job ID:", job_id)

    # Create the database job first.
    from app.db.database import SessionLocal
    from app.models.scraping import ScrapeJob

    db = SessionLocal()

    try:
        job = ScrapeJob(
            id=job_id,
            name="Service Layer Diagnostic Test",
            status="queued",
            target_count=len(urls),
            max_concurrency=3,
            proxy_configured=False,
            profile={
                "viewport_width": 1440,
                "viewport_height": 900,
                "locale": "en-US",
                "timezone_id": "Asia/Kolkata",
                "events": [],
            },
            selector_map=selector_map,
        )

        db.add(job)
        db.commit()

    finally:
        db.close()

    print("Database job created.")
    print("Running run_scrape_job()...")

    await run_scrape_job(
        job_id,
        urls,
        selector_map,
        config,
    )

    print()
    print("run_scrape_job() finished.")

    db = SessionLocal()

    try:
        job = db.get(ScrapeJob, job_id)

        print()
        print("FINAL JOB")
        print("Status:", job.status)
        print("Processed:", job.processed_count)
        print("Success:", job.success_count)
        print("Failed:", job.failed_count)
        print("RPS:", job.records_per_second)
        print("Error:", repr(job.error_message))

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())