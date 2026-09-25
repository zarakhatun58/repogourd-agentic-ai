from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Iterable

from app.services.scraper.models import ProxyConfig


@dataclass
class ProxyStats:
    """
    Runtime health information for one proxy.
    """

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blocked_requests: int = 0
    consecutive_failures: int = 0

    total_latency_ms: float = 0.0
    last_used_at: float | None = None
    last_success_at: float | None = None
    last_failure_at: float | None = None

    cooldown_until: float = 0.0

    @property
    def average_latency_ms(self) -> float:
        if self.successful_requests == 0:
            return 0.0

        return round(
            self.total_latency_ms / self.successful_requests,
            2,
        )

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0

        return round(
            self.failed_requests / self.total_requests,
            4,
        )

    @property
    def is_in_cooldown(self) -> bool:
        return time.monotonic() < self.cooldown_until

    def snapshot(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "blocked_requests": self.blocked_requests,
            "consecutive_failures": self.consecutive_failures,
            "average_latency_ms": self.average_latency_ms,
            "failure_rate": self.failure_rate,
            "last_used_at": self.last_used_at,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "cooldown_until": self.cooldown_until,
            "is_in_cooldown": self.is_in_cooldown,
        }


@dataclass
class ProxyEntry:
    """
    Proxy configuration plus runtime health state.
    """

    proxy: ProxyConfig
    proxy_id: str
    stats: ProxyStats = field(default_factory=ProxyStats)
    enabled: bool = True

    def snapshot(self) -> dict:
        return {
            "proxy_id": self.proxy_id,
            "server": self.proxy.server,
            "enabled": self.enabled,
            "stats": self.stats.snapshot(),
        }


class ProxyPool:
    """
    Thread-safe/async-safe proxy pool.

    Selection strategy:
    - Round-robin across healthy proxies.
    - Skip disabled proxies.
    - Skip proxies in cooldown.
    - Prefer proxies with fewer consecutive failures.

    This component only manages routing through configured proxies.
    It does not implement anti-bot bypassing.
    """

    def __init__(
        self,
        proxies: Iterable[ProxyConfig] | None = None,
        *,
        cooldown_seconds: float = 30.0,
        max_consecutive_failures: int = 3,
    ):
        self.cooldown_seconds = max(cooldown_seconds, 0.0)
        self.max_consecutive_failures = max(
            max_consecutive_failures,
            1,
        )

        self._entries: list[ProxyEntry] = []
        self._cursor = 0
        self._lock = asyncio.Lock()

        if proxies:
            self.add_many(proxies)

    def add(
        self,
        proxy: ProxyConfig,
        *,
        proxy_id: str | None = None,
    ) -> ProxyEntry:
        """
        Add a proxy to the pool.
        """
        identifier = proxy_id or self._make_proxy_id(proxy)

        existing = self.get(identifier)
        if existing:
            return existing

        entry = ProxyEntry(
            proxy=proxy,
            proxy_id=identifier,
        )

        self._entries.append(entry)
        return entry

    def add_many(
        self,
        proxies: Iterable[ProxyConfig],
    ) -> list[ProxyEntry]:
        entries = []

        for proxy in proxies:
            entries.append(self.add(proxy))

        return entries

    def remove(self, proxy_id: str) -> bool:
        """
        Remove a proxy from the pool.
        """
        original_length = len(self._entries)

        self._entries = [
            entry
            for entry in self._entries
            if entry.proxy_id != proxy_id
        ]

        if self._entries:
            self._cursor %= len(self._entries)
        else:
            self._cursor = 0

        return len(self._entries) < original_length

    def get(self, proxy_id: str) -> ProxyEntry | None:
        for entry in self._entries:
            if entry.proxy_id == proxy_id:
                return entry

        return None

    def enable(self, proxy_id: str) -> bool:
        entry = self.get(proxy_id)

        if not entry:
            return False

        entry.enabled = True
        entry.stats.consecutive_failures = 0
        entry.stats.cooldown_until = 0.0

        return True

    def disable(self, proxy_id: str) -> bool:
        entry = self.get(proxy_id)

        if not entry:
            return False

        entry.enabled = False
        return True

    async def acquire(self) -> ProxyEntry | None:
        """
        Select the next healthy proxy.

        Returns None when no healthy proxy is available.
        """
        async with self._lock:
            if not self._entries:
                return None

            now = time.monotonic()

            available = [
                entry
                for entry in self._entries
                if entry.enabled
                and entry.stats.cooldown_until <= now
            ]

            if not available:
                return None

            # Rotate through the complete pool while preferring healthy
            # entries with fewer consecutive failures.
            count = len(self._entries)

            for _ in range(count):
                entry = self._entries[self._cursor % count]
                self._cursor = (self._cursor + 1) % count

                if (
                    entry.enabled
                    and entry.stats.cooldown_until <= now
                ):
                    entry.stats.last_used_at = time.monotonic()
                    return entry

            # Fallback: choose the least-failing healthy proxy.
            available.sort(
                key=lambda item: (
                    item.stats.consecutive_failures,
                    item.stats.failure_rate,
                )
            )

            selected = available[0]
            selected.stats.last_used_at = time.monotonic()

            return selected

    async def acquire_config(self) -> ProxyConfig | None:
        entry = await self.acquire()

        if entry is None:
            return None

        return entry.proxy

    def record_success(
        self,
        proxy_id: str,
        *,
        latency_ms: float = 0.0,
    ) -> None:
        entry = self.get(proxy_id)

        if not entry:
            return

        stats = entry.stats

        stats.total_requests += 1
        stats.successful_requests += 1
        stats.total_latency_ms += max(latency_ms, 0.0)

        stats.consecutive_failures = 0
        stats.last_success_at = time.monotonic()
        stats.cooldown_until = 0.0

    def record_failure(
        self,
        proxy_id: str,
        *,
        latency_ms: float = 0.0,
        blocked: bool = False,
    ) -> None:
        entry = self.get(proxy_id)

        if not entry:
            return

        stats = entry.stats

        stats.total_requests += 1
        stats.failed_requests += 1
        stats.consecutive_failures += 1
        stats.last_failure_at = time.monotonic()

        if blocked:
            stats.blocked_requests += 1

        if stats.consecutive_failures >= self.max_consecutive_failures:
            stats.cooldown_until = (
                time.monotonic()
                + self.cooldown_seconds
            )

    def healthy_count(self) -> int:
        now = time.monotonic()

        return sum(
            1
            for entry in self._entries
            if entry.enabled
            and entry.stats.cooldown_until <= now
        )

    def total_count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._cursor = 0

    def snapshots(self) -> list[dict]:
        return [
            entry.snapshot()
            for entry in self._entries
        ]

    def snapshot(self) -> dict:
        return {
            "total": self.total_count(),
            "healthy": self.healthy_count(),
            "cooldown_seconds": self.cooldown_seconds,
            "max_consecutive_failures": self.max_consecutive_failures,
            "proxies": self.snapshots(),
        }

    @staticmethod
    def _make_proxy_id(proxy: ProxyConfig) -> str:
        """
        Generate a stable non-secret identifier.

        Credentials are deliberately excluded.
        """
        value = proxy.server.strip().lower()

        return value.replace(
            "://",
            "_",
        ).replace(
            ":",
            "_",
        ).replace(
            "/",
            "_",
        )


class ProxyRotator:
    """
    Lightweight proxy rotation helper.

    The rotator obtains a proxy from the pool and records the result
    after the request has completed.
    """

    def __init__(self, pool: ProxyPool):
        self.pool = pool

    async def next_proxy(self) -> ProxyEntry | None:
        return await self.pool.acquire()

    async def next_config(self) -> ProxyConfig | None:
        return await self.pool.acquire_config()

    def success(
        self,
        proxy_id: str,
        *,
        latency_ms: float = 0.0,
    ) -> None:
        self.pool.record_success(
            proxy_id,
            latency_ms=latency_ms,
        )

    def failure(
        self,
        proxy_id: str,
        *,
        latency_ms: float = 0.0,
        blocked: bool = False,
    ) -> None:
        self.pool.record_failure(
            proxy_id,
            latency_ms=latency_ms,
            blocked=blocked,
        )