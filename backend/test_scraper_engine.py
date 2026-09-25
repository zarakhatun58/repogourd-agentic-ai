import asyncio

from app.services.scraper.manager import ScrapeManager
from app.services.scraper.manager import ScrapeManagerConfig


async def main():
    print("Starting ScrapeManager test...")

    config = ScrapeManagerConfig(
        worker_count=3,
        max_retries=1,
        retry_delay_ms=250,
        navigation_timeout_ms=15000,
        headless=True,
    )

    manager = ScrapeManager(
        config=config,
        selector_map={
            "title": ".item-title",
            "description": ".item-description",
            "price": ".price",
            "category": ".category",
            "item_id": ".item-id",
        },
    )

    urls = [
        "http://127.0.0.1:8100/item/1",
        "http://127.0.0.1:8100/item/2",
        "http://127.0.0.1:8100/item/3",
    ]

    try:
        print("Running scraper...")
        run = await manager.run(urls, run_id="diagnostic-test")

        print()
        print("Scrape completed")
        print("Status:", run.status)
        print("Targets:", len(run.targets))
        print("Results:", len(run.results))

        for result in run.results:
            print()
            print("URL:", result.url)
            print("Status:", result.status)
            print("HTTP:", result.http_status)
            print("Worker:", result.worker_id)
            print("Latency:", result.latency_ms)
            print("Data:", result.data)
            print("Error:", result.error)

        print()
        print("Metrics:")
        print(manager.metrics.snapshot())

    except Exception as exc:
        print()
        print("SCRAPER ENGINE FAILED")
        print("Exception type:", type(exc).__name__)
        print("Exception repr:", repr(exc))
        print("Exception text:", str(exc))

        raise


if __name__ == "__main__":
    asyncio.run(main())