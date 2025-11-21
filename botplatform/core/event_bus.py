from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, DefaultDict, List

from botplatform.core.events import Event


class EventBus:
    """Простая асинхронная шина событий."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers: DefaultDict[str, List[Callable[[Event], Awaitable[None]]]] = defaultdict(list)
        self._running: bool = False
        self._task: asyncio.Task | None = None

    async def publish(self, event: Event) -> None:
        await self._queue.put(event)

    def subscribe(self, event_type: str, callback: Callable[[Event], Awaitable[None]]) -> None:
        self._subscribers[event_type].append(callback)

    async def _loop(self) -> None:
        self._running = True
        while self._running:
            event = await self._queue.get()
            callbacks = list(self._subscribers.get(event.type, []))
            for cb in callbacks:
                try:
                    await cb(event)
                except Exception as exc:  # noqa: BLE001
                    print(f"[EventBus] Error in subscriber {cb}: {exc!r}")

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
