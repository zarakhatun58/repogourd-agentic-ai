from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class QueueItem(Generic[T]):
    """
    One item waiting to be processed by a scraping worker.
    """

    item: T
    index: int


class ScrapeQueue(Generic[T]):
    """
    Async bounded queue for scraping targets.

    The queue provides:
    - bounded memory usage
    - async producers/consumers
    - graceful shutdown
    - queue size visibility
    """

    def __init__(self, maxsize: int = 0):
        if maxsize < 0:
            raise ValueError("maxsize cannot be negative")

        self._queue: asyncio.Queue[QueueItem[T] | None] = asyncio.Queue(
            maxsize=maxsize
        )

        self._closed = False
        self._produced = 0
        self._consumed = 0

    async def put(self, item: T, index: int) -> None:
        """
        Add a target to the queue.
        """

        if self._closed:
            raise RuntimeError("Cannot add items to a closed scrape queue")

        await self._queue.put(
            QueueItem(
                item=item,
                index=index,
            )
        )

        self._produced += 1

    async def get(self) -> QueueItem[T] | None:
        """
        Wait for the next item.

        None is used as a worker shutdown sentinel.
        """

        item = await self._queue.get()

        if item is None:
            self._queue.task_done()
            return None

        self._consumed += 1

        return item

    def task_done(self) -> None:
        """
        Mark the current queue item as completed.
        """

        self._queue.task_done()

    async def wait_until_empty(self) -> None:
        """
        Wait until every queued item has been processed.
        """

        await self._queue.join()

    async def close(self, worker_count: int = 1) -> None:
        """
        Stop workers by placing shutdown sentinels in the queue.
        """

        if self._closed:
            return

        self._closed = True

        for _ in range(max(worker_count, 1)):
            await self._queue.put(None)

    @property
    def size(self) -> int:
        return self._queue.qsize()

    @property
    def produced_count(self) -> int:
        return self._produced

    @property
    def consumed_count(self) -> int:
        return self._consumed

    @property
    def is_closed(self) -> bool:
        return self._closed

    def snapshot(self) -> dict:
        """
        Return queue metrics suitable for API/dashboard output.
        """

        return {
            "size": self.size,
            "produced_count": self.produced_count,
            "consumed_count": self.consumed_count,
            "closed": self.is_closed,
        }


async def populate_queue(
    queue: ScrapeQueue[T],
    items: list[T],
) -> None:
    """
    Add a list of targets to the queue.
    """

    for index, item in enumerate(items):
        await queue.put(
            item=item,
            index=index,
        )


async def drain_queue(
    queue: ScrapeQueue[T],
) -> None:
    """
    Wait until all queued work has been completed.
    """

    await queue.wait_until_empty()