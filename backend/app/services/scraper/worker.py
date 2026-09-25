from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.services.scraper.browser import BrowserManager
from app.services.scraper.extractor import PageExtractor
from app.services.scraper.metrics import ScrapeMetrics, WorkerMetrics
from app.services.scraper.models import ScrapeResult, ScrapeTarget
from app.services.scraper.proxy import ProxyEntry, ProxyPool
from app.services.scraper.queue import QueueItem, ScrapeQueue


@dataclass
class WorkerConfig:
    worker_count: int = 5
    max_retries: int = 2
    retry_delay_ms: int = 500
    navigation_timeout_ms: int = 15000
    wait_until: str = "domcontentloaded"


ResultCallback = Callable[[ScrapeResult], Awaitable[None]]


class ScrapeWorkerPool:
    """
    Concurrent Playwright scraping worker pool.

    Responsibilities:
    - Consume targets from ScrapeQueue.
    - Run concurrent Playwright workers.
    - Create isolated browser contexts per attempt.
    - Generate unique session identifiers.
    - Select proxies from an optional ProxyPool.
    - Navigate to authorized targets.
    - Extract structured data.
    - Retry transient failures.
    - Detect blocked/challenge responses.
    - Record global, worker, and proxy metrics.
    - Attach execution telemetry to structured JSON output.

    Security model:
    - Only authorized targets should be supplied.
    - Challenge detection is supported.
    - Security controls are not bypassed.
    """

    def __init__(
        self,
        *,
        queue: ScrapeQueue[ScrapeTarget],
        browser_manager: BrowserManager,
        extractor: PageExtractor,
        config: WorkerConfig | None = None,
        metrics: ScrapeMetrics | None = None,
        on_result: ResultCallback | None = None,
        proxy_pool: ProxyPool | None = None,
    ):
        self.queue = queue
        self.browser_manager = browser_manager
        self.extractor = extractor
        self.config = config or WorkerConfig()
        self.metrics = metrics or ScrapeMetrics()
        self.on_result = on_result
        self.proxy_pool = proxy_pool

        self.worker_metrics = [
            WorkerMetrics(
                worker_id=f"worker-{index + 1}"
            )
            for index in range(
                self.config.worker_count
            )
        ]

        self._tasks: list[asyncio.Task] = []

        # Runtime counters used by the live scraping dashboard
        # and technical demonstration.
        self._started_targets = 0
        self._completed_targets = 0
        self._active_targets = 0
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """
        Start all workers.
        """

        if self._tasks:
            raise RuntimeError(
                "Worker pool is already running"
            )

        if self.config.worker_count < 1:
            raise ValueError(
                "worker_count must be at least 1"
            )

        if not self.browser_manager.is_running:
            await self.browser_manager.start()

        self._tasks = [
            asyncio.create_task(
                self._worker_loop(worker_index),
                name=(
                    f"scrape-worker-"
                    f"{worker_index + 1}"
                ),
            )
            for worker_index in range(
                self.config.worker_count
            )
        ]

    async def wait(self) -> None:
        """
        Wait until all queued scrape items are processed.
        """

        if not self._tasks:
            return

        await self.queue.wait_until_empty()

        await self.queue.close(
            worker_count=self.config.worker_count
        )

        await asyncio.gather(
            *self._tasks,
            return_exceptions=False,
        )

        self._tasks = []

    async def stop(self) -> None:
        """
        Stop the worker pool and cancel active workers.
        """

        if not self._tasks:
            return

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(
            *self._tasks,
            return_exceptions=True,
        )

        self._tasks = []

    async def _worker_loop(
        self,
        worker_index: int,
    ) -> None:
        worker_id = (
            f"worker-{worker_index + 1}"
        )

        metrics = self.worker_metrics[
            worker_index
        ]

        while True:
            item = await self.queue.get()

            if item is None:
                return

            try:
                result = await self._process_item(
                    item=item,
                    worker_id=worker_id,
                    worker_metrics=metrics,
                )

                if self.on_result:
                    await self.on_result(result)

            finally:
                self.queue.task_done()

    async def _process_item(
        self,
        *,
        item: QueueItem[ScrapeTarget],
        worker_id: str,
        worker_metrics: WorkerMetrics,
    ) -> ScrapeResult:
        target = item.item

        target.index = item.index
        target.worker_id = worker_id
        target.proxy_id = None
        target.status = "running"
        target.started_at = (
            datetime.now(timezone.utc)
        )

        async with self._lock:
            self._started_targets += 1
            self._active_targets += 1

        result: ScrapeResult | None = None

        try:
            for attempt in range(
                self.config.max_retries + 1
            ):
                result = await self._scrape_attempt(
                    target=target,
                    worker_id=worker_id,
                    attempt=attempt,
                )

                if self._should_retry(
                    result,
                    attempt,
                ):
                    await asyncio.sleep(
                        self.config.retry_delay_ms
                        * (attempt + 1)
                        / 1000
                    )

                    continue

                break

            if result is None:
                result = ScrapeResult(
                    url=target.url,
                    status="failed",
                    worker_id=worker_id,
                    error=(
                        "Scrape worker produced "
                        "no result"
                    ),
                    proxy_id=None,
                    created_at=datetime.now(
                        timezone.utc
                    ),
                )

            target.completed_at = (
                datetime.now(timezone.utc)
            )

            target.status = result.status
            target.http_status = result.http_status
            target.latency_ms = result.latency_ms
            target.data = result.data
            target.error = result.error
            target.proxy_id = result.proxy_id

            worker_metrics.record(
                success=result.status == "success",
                latency_ms=result.latency_ms or 0.0,
            )

            if result.status == "success":
                self.metrics.record_success(
                    result.latency_ms or 0.0,
                    retry_count=result.retry_count,
                )
            else:
                self.metrics.record_failure(
                    result.latency_ms or 0.0,
                    retry_count=result.retry_count,
                    timeout=self._is_timeout(
                        result.error
                    ),
                    blocked=(
                        result.blocked
                        or result.challenge_detected
                    ),
                )

            return result

        finally:
            async with self._lock:
                self._active_targets = max(
                    0,
                    self._active_targets - 1,
                )
                self._completed_targets += 1

    async def _scrape_attempt(
        self,
        *,
        target: ScrapeTarget,
        worker_id: str,
        attempt: int,
    ) -> ScrapeResult:
        started = (
            asyncio.get_running_loop().time()
        )

        context = None
        proxy_entry: ProxyEntry | None = None

        # Every Playwright context receives a unique
        # session identifier. This allows the live
        # demonstration to show session isolation.
        session_id = (
            f"{worker_id}-"
            f"{uuid.uuid4().hex[:12]}"
        )

        try:
            # Acquire a proxy for this attempt.
            #
            # If no ProxyPool exists, proxy_entry
            # remains None and BrowserManager uses
            # direct or fixed-proxy mode.
            if self.proxy_pool is not None:
                proxy_entry = (
                    await self.proxy_pool.acquire()
                )

                if proxy_entry is None:
                    return self._build_failed_result(
                        target=target,
                        worker_id=worker_id,
                        attempt=attempt,
                        started=started,
                        error=(
                            "No healthy proxy "
                            "is currently available."
                        ),
                        session_id=session_id,
                        proxy_id=None,
                    )

            # Store the selected proxy on the target.
            target.proxy_id = (
                proxy_entry.proxy_id
                if proxy_entry
                else None
            )

            context = (
                await self.browser_manager.create_context(
                    proxy_entry=proxy_entry,
                )
            )

            page = await context.new_page()

            page.set_default_timeout(
                self.config.navigation_timeout_ms
            )

            response = await page.goto(
                target.url,
                wait_until=self.config.wait_until,
                timeout=(
                    self.config.navigation_timeout_ms
                ),
            )

            http_status = (
                response.status
                if response
                else None
            )

            extraction = (
                await self.extractor.extract(page)
            )

            latency_ms = round(
                (
                    asyncio.get_running_loop().time()
                    - started
                )
                * 1000,
                2,
            )

            current_proxy_id = (
                proxy_entry.proxy_id
                if proxy_entry
                else None
            )

            # Challenge / blocked target.
            if (
                extraction.blocked
                or extraction.challenge_detected
            ):
                target.status = "blocked"

                if proxy_entry is not None:
                    self.proxy_pool.record_failure(
                        proxy_entry.proxy_id,
                        latency_ms=latency_ms,
                        blocked=True,
                    )

                data = self._attach_runtime_metadata(
                    data=extraction.data,
                    worker_id=worker_id,
                    session_id=session_id,
                    proxy_id=current_proxy_id,
                    attempt=attempt,
                    http_status=http_status,
                    latency_ms=latency_ms,
                    status="blocked",
                    challenge_detected=(
                        extraction.challenge_detected
                    ),
                    blocked=extraction.blocked,
                )

                return ScrapeResult(
                    url=target.url,
                    status="failed",
                    worker_id=worker_id,
                    http_status=http_status,
                    latency_ms=latency_ms,
                    data=data,
                    error=(
                        "Target challenge detected: "
                        f"{extraction.challenge_type or 'unknown'}"
                    ),
                    retry_count=attempt,
                    blocked=extraction.blocked,
                    challenge_detected=(
                        extraction.challenge_detected
                    ),
                    proxy_id=current_proxy_id,
                    created_at=(
                        datetime.now(
                            timezone.utc
                        )
                    ),
                )

            # Treat all HTTP 400+ responses as failures.
            if (
                http_status is not None
                and http_status >= 400
            ):
                is_blocked = http_status in {
                    401,
                    403,
                    429,
                }

                if proxy_entry is not None:
                    self.proxy_pool.record_failure(
                        proxy_entry.proxy_id,
                        latency_ms=latency_ms,
                        blocked=is_blocked,
                    )

                data = self._attach_runtime_metadata(
                    data=None,
                    worker_id=worker_id,
                    session_id=session_id,
                    proxy_id=current_proxy_id,
                    attempt=attempt,
                    http_status=http_status,
                    latency_ms=latency_ms,
                    status="failed",
                    challenge_detected=False,
                    blocked=is_blocked,
                )

                return ScrapeResult(
                    url=target.url,
                    status="failed",
                    worker_id=worker_id,
                    http_status=http_status,
                    latency_ms=latency_ms,
                    data=data,
                    error=(
                        f"Target returned HTTP "
                        f"{http_status}"
                    ),
                    retry_count=attempt,
                    blocked=is_blocked,
                    challenge_detected=False,
                    proxy_id=current_proxy_id,
                    created_at=(
                        datetime.now(
                            timezone.utc
                        )
                    ),
                )

            # Successful request.
            if proxy_entry is not None:
                self.proxy_pool.record_success(
                    proxy_entry.proxy_id,
                    latency_ms=latency_ms,
                )

            data = self._attach_runtime_metadata(
                data=extraction.data,
                worker_id=worker_id,
                session_id=session_id,
                proxy_id=current_proxy_id,
                attempt=attempt,
                http_status=http_status,
                latency_ms=latency_ms,
                status="success",
                challenge_detected=False,
                blocked=False,
            )

            return ScrapeResult(
                url=target.url,
                status="success",
                worker_id=worker_id,
                http_status=http_status,
                latency_ms=latency_ms,
                data=data,
                error=None,
                retry_count=attempt,
                blocked=False,
                challenge_detected=False,
                proxy_id=current_proxy_id,
                created_at=(
                    datetime.now(
                        timezone.utc
                    )
                ),
            )

        except PlaywrightTimeoutError as exc:
            latency_ms = round(
                (
                    asyncio.get_running_loop().time()
                    - started
                )
                * 1000,
                2,
            )

            current_proxy_id = (
                proxy_entry.proxy_id
                if proxy_entry
                else None
            )

            if proxy_entry is not None:
                self.proxy_pool.record_failure(
                    proxy_entry.proxy_id,
                    latency_ms=latency_ms,
                )

            return self._build_failed_result(
                target=target,
                worker_id=worker_id,
                attempt=attempt,
                started=started,
                latency_ms=latency_ms,
                error=(
                    f"Timeout: {str(exc)[:500]}"
                ),
                session_id=session_id,
                proxy_id=current_proxy_id,
            )

        except Exception as exc:
            latency_ms = round(
                (
                    asyncio.get_running_loop().time()
                    - started
                )
                * 1000,
                2,
            )

            current_proxy_id = (
                proxy_entry.proxy_id
                if proxy_entry
                else None
            )

            if proxy_entry is not None:
                self.proxy_pool.record_failure(
                    proxy_entry.proxy_id,
                    latency_ms=latency_ms,
                )

            return self._build_failed_result(
                target=target,
                worker_id=worker_id,
                attempt=attempt,
                started=started,
                latency_ms=latency_ms,
                error=(
                    f"{type(exc).__name__}: "
                    f"{str(exc)[:500]}"
                ),
                session_id=session_id,
                proxy_id=current_proxy_id,
            )

        finally:
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass

    @staticmethod
    def _attach_runtime_metadata(
        *,
        data: dict | None,
        worker_id: str,
        session_id: str,
        proxy_id: str | None,
        attempt: int,
        http_status: int | None,
        latency_ms: float,
        status: str,
        challenge_detected: bool,
        blocked: bool,
    ) -> dict:
        """
        Add execution telemetry to the structured JSON
        record without changing the database schema.

        The application data remains intact under its
        original keys while `_scrape_runtime` provides
        evidence of worker/session/proxy execution.
        """

        result = dict(data or {})

        result["_scrape_runtime"] = {
            "worker_id": worker_id,
            "session_id": session_id,
            "proxy_id": proxy_id,
            "attempt": attempt + 1,
            "http_status": http_status,
            "latency_ms": latency_ms,
            "status": status,
            "blocked": blocked,
            "challenge_detected": challenge_detected,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        return result

    def _build_failed_result(
        self,
        *,
        target: ScrapeTarget,
        worker_id: str,
        attempt: int,
        started: float,
        error: str,
        session_id: str,
        proxy_id: str | None,
        latency_ms: float | None = None,
    ) -> ScrapeResult:
        if latency_ms is None:
            latency_ms = round(
                (
                    asyncio.get_running_loop().time()
                    - started
                )
                * 1000,
                2,
            )

        data = self._attach_runtime_metadata(
            data=None,
            worker_id=worker_id,
            session_id=session_id,
            proxy_id=proxy_id,
            attempt=attempt,
            http_status=None,
            latency_ms=latency_ms,
            status="failed",
            challenge_detected=False,
            blocked=False,
        )

        return ScrapeResult(
            url=target.url,
            status="failed",
            worker_id=worker_id,
            latency_ms=latency_ms,
            data=data,
            error=error,
            retry_count=attempt,
            blocked=False,
            challenge_detected=False,
            proxy_id=proxy_id,
            created_at=datetime.now(
                timezone.utc
            ),
        )

    def _should_retry(
        self,
        result: ScrapeResult,
        attempt: int,
    ) -> bool:
        """
        Retry only transient failures.

        Challenges and explicit access-denied responses
        are not bypassed.
        """

        if result.status == "success":
            return False

        if attempt >= self.config.max_retries:
            return False

        if (
            result.blocked
            or result.challenge_detected
        ):
            return False

        if result.http_status in {
            400,
            401,
            403,
            404,
        }:
            return False

        if result.http_status in {
            408,
            425,
            429,
        }:
            return True

        if (
            result.http_status is not None
            and result.http_status >= 500
        ):
            return True

        if self._is_timeout(result.error):
            return True

        if result.error:
            transient_errors = (
                "connection",
                "network",
                "target closed",
                "browser",
                "timeout",
                "temporarily",
                "proxy",
            )

            error_lower = (
                result.error.lower()
            )

            return any(
                marker in error_lower
                for marker in transient_errors
            )

        return False

    @staticmethod
    def _is_timeout(
        error: str | None,
    ) -> bool:
        if not error:
            return False

        return "timeout" in error.lower()

    def snapshot(self) -> dict:
        snapshot = {
            "workers": [
                worker.snapshot()
                for worker in self.worker_metrics
            ],
            "global": self.metrics.snapshot(),
            "queue": self.queue.snapshot(),
            "running": bool(self._tasks),
            "execution": {
                "worker_count": self.config.worker_count,
                "started_targets": self._started_targets,
                "completed_targets": self._completed_targets,
                "active_targets": self._active_targets,
            },
        }

        if self.proxy_pool is not None:
            snapshot["proxy_pool"] = (
                self.proxy_pool.snapshot()
            )

        return snapshot


async def run_worker_pool(
    *,
    queue: ScrapeQueue[ScrapeTarget],
    browser_manager: BrowserManager,
    extractor: PageExtractor,
    config: WorkerConfig | None = None,
    metrics: ScrapeMetrics | None = None,
    on_result: ResultCallback | None = None,
    proxy_pool: ProxyPool | None = None,
) -> ScrapeWorkerPool:
    """
    Convenience function for running a complete worker pool.
    """

    pool = ScrapeWorkerPool(
        queue=queue,
        browser_manager=browser_manager,
        extractor=extractor,
        config=config,
        metrics=metrics,
        on_result=on_result,
        proxy_pool=proxy_pool,
    )

    await pool.start()
    await pool.wait()

    return pool