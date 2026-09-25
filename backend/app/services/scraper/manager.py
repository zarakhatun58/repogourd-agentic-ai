from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.services.scraper.browser import BrowserManager
from app.services.scraper.extractor import PageExtractor
from app.services.scraper.metrics import ScrapeMetrics
from app.services.scraper.models import (
    BrowserProfile,
    ProxyConfig,
    ScrapeResult,
    ScrapeTarget,
)
from app.services.scraper.proxy import ProxyPool
from app.services.scraper.queue import ScrapeQueue, populate_queue
from app.services.scraper.worker import ScrapeWorkerPool, WorkerConfig


ResultCallback = Callable[[ScrapeResult], Awaitable[None]]


@dataclass
class ScrapeManagerConfig:
    """
    High-level scraper configuration.

    Supports:
    - Direct connections
    - One fixed proxy
    - Multiple rotating proxies
    - Browser profiles
    - Bounded worker concurrency
    - Retry and timeout configuration
    """

    worker_count: int = 5
    max_retries: int = 2
    retry_delay_ms: int = 500
    navigation_timeout_ms: int = 15000

    queue_maxsize: int = 0

    viewport_width: int = 1440
    viewport_height: int = 900
    locale: str = "en-US"
    timezone_id: str = "Asia/Kolkata"

    user_agent: str | None = None
    is_mobile: bool = False
    has_touch: bool = False
    device_scale_factor: float = 1.0
    color_scheme: str = "light"

    # Fixed proxy mode.
    proxy_url: str | None = None
    proxy_username: str | None = None
    proxy_password: str | None = None

    # Proxy pool mode.
    proxy_urls: list[str] = field(default_factory=list)

    proxy_cooldown_seconds: float = 30.0
    proxy_max_consecutive_failures: int = 3

    headless: bool = True


@dataclass
class ScrapeRun:
    """
    In-memory state for one scraper execution.
    """

    run_id: str
    targets: list[ScrapeTarget] = field(default_factory=list)
    results: list[ScrapeResult] = field(default_factory=list)
    metrics: ScrapeMetrics | None = None

    status: str = "created"

    def snapshot(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "target_count": len(self.targets),
            "result_count": len(self.results),
            "metrics": self.metrics.snapshot()
            if self.metrics
            else {},
        }


class ScrapeManager:
    """
    Main orchestration layer for RepoGuard's scraping engine.

    Flow:

        URLs
          ↓
        ScrapeTarget
          ↓
        ScrapeQueue
          ↓
        ScrapeWorkerPool
          ↓
        BrowserManager
          ↓
        ProxyPool (optional)
          ↓
        Playwright
          ↓
        PageExtractor
          ↓
        ScrapeResult
          ↓
        Metrics / callback
    """

    def __init__(
        self,
        *,
        config: ScrapeManagerConfig | None = None,
        selector_map: dict[str, str] | None = None,
        on_result: ResultCallback | None = None,
    ):
        self.config = config or ScrapeManagerConfig()
        self.selector_map = selector_map or {}
        self.on_result = on_result

        self.queue: ScrapeQueue[ScrapeTarget] = ScrapeQueue(
            maxsize=self.config.queue_maxsize
        )

        self.metrics = ScrapeMetrics()

        self.proxy_pool = self._build_proxy_pool()

        self.browser_manager = BrowserManager(
            headless=self.config.headless,
            browser_profile=BrowserProfile(
                viewport_width=self.config.viewport_width,
                viewport_height=self.config.viewport_height,
                locale=self.config.locale,
                timezone_id=self.config.timezone_id,
                user_agent=self.config.user_agent,
                is_mobile=self.config.is_mobile,
                has_touch=self.config.has_touch,
                device_scale_factor=self.config.device_scale_factor,
                color_scheme=self.config.color_scheme,
            ),
            proxy=self._build_fixed_proxy(),
            proxy_pool=self.proxy_pool,
        )

        self.extractor = PageExtractor(
            selector_map=self.selector_map
        )

        self.worker_pool: ScrapeWorkerPool | None = None
        self.current_run: ScrapeRun | None = None

    def _build_fixed_proxy(self) -> ProxyConfig | None:
        """
        Build the legacy single-proxy configuration.

        This remains available when proxy_urls is empty.
        """

        if not self.config.proxy_url:
            return None

        return ProxyConfig(
            server=self.config.proxy_url,
            username=self.config.proxy_username,
            password=self.config.proxy_password,
        )

    def _build_proxy_pool(self) -> ProxyPool | None:
        """
        Build a rotating proxy pool when multiple proxy URLs
        are explicitly configured.

        Proxy credentials are intentionally not inferred from
        arbitrary URLs. Authentication can be added later through
        a dedicated proxy configuration model.
        """

        if not self.config.proxy_urls:
            return None

        proxies = [
            ProxyConfig(server=url)
            for url in self.config.proxy_urls
            if url and url.strip()
        ]

        if not proxies:
            return None

        return ProxyPool(
            proxies,
            cooldown_seconds=self.config.proxy_cooldown_seconds,
            max_consecutive_failures=(
                self.config.proxy_max_consecutive_failures
            ),
        )

    async def run(
        self,
        urls: list[str],
        *,
        run_id: str | None = None,
    ) -> ScrapeRun:
        """
        Execute a complete scraping run.
        """

        if not urls:
            raise ValueError("At least one URL is required")

        if (
            self.current_run
            and self.current_run.status == "running"
        ):
            raise RuntimeError(
                "A scrape run is already running"
            )

        run = ScrapeRun(
            run_id=run_id or str(uuid.uuid4()),
            targets=[
                ScrapeTarget(
                    url=url,
                    index=index,
                )
                for index, url in enumerate(urls)
            ],
            metrics=self.metrics,
            status="queued",
        )

        self.current_run = run

        try:
            await populate_queue(
                self.queue,
                run.targets,
            )

            run.status = "running"

            worker_config = WorkerConfig(
                worker_count=self.config.worker_count,
                max_retries=self.config.max_retries,
                retry_delay_ms=self.config.retry_delay_ms,
                navigation_timeout_ms=(
                    self.config.navigation_timeout_ms
                ),
            )

            self.worker_pool = ScrapeWorkerPool(
                queue=self.queue,
                browser_manager=self.browser_manager,
                extractor=self.extractor,
                config=worker_config,
                metrics=self.metrics,
                on_result=self._handle_result,
                proxy_pool=self.proxy_pool,
            )

            await self.worker_pool.start()
            await self.worker_pool.wait()

            run.status = "completed"

        except asyncio.CancelledError:
            run.status = "cancelled"
            raise

        except Exception:
            run.status = "failed"
            raise

        finally:
            await self.shutdown()

        return run

    async def _handle_result(
        self,
        result: ScrapeResult,
    ) -> None:
        if self.current_run is not None:
            self.current_run.results.append(result)

        if self.on_result:
            await self.on_result(result)

    async def start(self) -> None:
        """
        Start browser infrastructure without processing URLs.
        """

        if not self.browser_manager.is_running:
            await self.browser_manager.start()

    async def add_targets(
        self,
        urls: list[str],
    ) -> list[ScrapeTarget]:
        """
        Add additional URLs to the queue.
        """

        if not urls:
            return []

        targets = [
            ScrapeTarget(
                url=url,
                index=index,
            )
            for index, url in enumerate(urls)
        ]

        await populate_queue(
            self.queue,
            targets,
        )

        if self.current_run:
            self.current_run.targets.extend(
                targets
            )

        return targets

    async def shutdown(self) -> None:
        """
        Stop workers and close all browser instances cleanly.
        """

        if self.worker_pool is not None:
            await self.worker_pool.stop()
            self.worker_pool = None

        if self.browser_manager.is_running:
            await self.browser_manager.stop()

    def snapshot(self) -> dict[str, Any]:
        """
        Return a dashboard-friendly snapshot.
        """

        run_snapshot = (
            self.current_run.snapshot()
            if self.current_run
            else None
        )

        worker_snapshot = (
            self.worker_pool.snapshot()
            if self.worker_pool
            else None
        )

        return {
            "run": run_snapshot,
            "workers": worker_snapshot,
            "metrics": self.metrics.snapshot(),
            "queue": self.queue.snapshot(),
            "browser": {
                "running": self.browser_manager.is_running,
                "headless": self.config.headless,
                "proxy_configured": bool(
                    self.config.proxy_url
                    or self.proxy_pool
                ),
                "proxy_pool_enabled": (
                    self.proxy_pool is not None
                ),
                "proxy_pool": (
                    self.proxy_pool.snapshot()
                    if self.proxy_pool
                    else None
                ),
                "proxy_browser_count": (
                    self.browser_manager.proxy_browser_count
                ),
            },
        }


async def run_scrape(
    urls: list[str],
    *,
    selector_map: dict[str, str] | None = None,
    config: ScrapeManagerConfig | None = None,
    run_id: str | None = None,
    on_result: ResultCallback | None = None,
) -> ScrapeRun:
    """
    Convenience API for executing a complete scraping run.
    """

    manager = ScrapeManager(
        config=config,
        selector_map=selector_map,
        on_result=on_result,
    )

    return await manager.run(
        urls,
        run_id=run_id,
    )