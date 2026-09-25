from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field


@dataclass
class ScrapeMetrics:
    """
    Runtime metrics for a scraping job.

    These metrics are kept in memory while the job is running.
    Persistent job-level metrics are written to PostgreSQL by the
    scraper service/worker layer.
    """

    started_at: float = field(default_factory=time.perf_counter)

    processed_count: int = 0
    success_count: int = 0
    failed_count: int = 0

    blocked_count: int = 0
    retry_count: int = 0
    timeout_count: int = 0

    latencies_ms: list[float] = field(default_factory=list)

    def record_success(
        self,
        latency_ms: float,
        *,
        retry_count: int = 0,
    ) -> None:
        self.processed_count += 1
        self.success_count += 1
        self.retry_count += retry_count
        self.latencies_ms.append(latency_ms)

    def record_failure(
        self,
        latency_ms: float,
        *,
        retry_count: int = 0,
        timeout: bool = False,
        blocked: bool = False,
    ) -> None:
        self.processed_count += 1
        self.failed_count += 1
        self.retry_count += retry_count

        if timeout:
            self.timeout_count += 1

        if blocked:
            self.blocked_count += 1

        self.latencies_ms.append(latency_ms)

    @property
    def elapsed_seconds(self) -> float:
        return max(time.perf_counter() - self.started_at, 0.001)

    @property
    def records_per_second(self) -> float:
        return round(
            self.processed_count / self.elapsed_seconds,
            2,
        )

    @property
    def average_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0

        return round(
            statistics.mean(self.latencies_ms),
            2,
        )

    @property
    def p50_latency_ms(self) -> float:
        return self._percentile(50)

    @property
    def p95_latency_ms(self) -> float:
        return self._percentile(95)

    @property
    def p99_latency_ms(self) -> float:
        return self._percentile(99)

    def _percentile(self, percentile: int) -> float:
        if not self.latencies_ms:
            return 0.0

        values = sorted(self.latencies_ms)

        if len(values) == 1:
            return round(values[0], 2)

        index = (len(values) - 1) * percentile / 100
        lower = int(index)
        upper = min(lower + 1, len(values) - 1)

        fraction = index - lower

        value = (
            values[lower]
            + (values[upper] - values[lower]) * fraction
        )

        return round(value, 2)

    def snapshot(self) -> dict:
        """
        Return a JSON-serializable metrics snapshot.
        """

        return {
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "blocked_count": self.blocked_count,
            "retry_count": self.retry_count,
            "timeout_count": self.timeout_count,
            "records_per_second": self.records_per_second,
            "average_latency_ms": self.average_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "elapsed_seconds": round(
                self.elapsed_seconds,
                3,
            ),
        }


class WorkerMetrics:
    """
    Metrics for individual scraping workers.
    """

    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.processed_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.total_latency_ms = 0.0

    def record(
        self,
        *,
        success: bool,
        latency_ms: float,
    ) -> None:
        self.processed_count += 1
        self.total_latency_ms += latency_ms

        if success:
            self.success_count += 1
        else:
            self.failed_count += 1

    @property
    def average_latency_ms(self) -> float:
        if self.processed_count == 0:
            return 0.0

        return round(
            self.total_latency_ms / self.processed_count,
            2,
        )

    def snapshot(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "average_latency_ms": self.average_latency_ms,
        }


class Timer:
    """
    Small helper for measuring operation latency.
    """

    def __init__(self):
        self.started_at = time.perf_counter()

    def elapsed_ms(self) -> float:
        return round(
            (time.perf_counter() - self.started_at) * 1000,
            2,
        )