# botplatform/core/event_bus.py

from __future__ import annotations
import asyncio
import time
from typing import Callable, Dict, List, Awaitable, Any, DefaultDict
from collections import defaultdict

from pydantic import BaseModel
from botplatform.core.events import Event


class EventBus:
    """
    Простая асинхронная шина событий.

    Возможности:
    - publish(event): публикует событие в очередь
    - subscribe(event_type, callback): подписка на события выбранного типа
    - start(): запускает обработку событий
    - stop(): останавливает цикл
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers: DefaultDict[str, List[Callable[[Event], Awaitable[None]]]] = defaultdict(list)
        self._running = False
        self._task: asyncio.Task | None = None

    async def publish(self, event: Event) -> None:
        """Добавить событие в очередь для обработки."""
        await self._queue.put(event)

    def subscribe(self, event_type: str, callback: Callable[[Event], Awaitable[None]]) -> None:
        """Подписать callback на события определенного типа."""
        self._subscribers[event_type].append(callback)

    async def _run(self) -> None:
        self._running = True
        while self._running:
            event = await self._queue.get()
            callbacks = self._subscribers.get(event.type, [])
            for cb in callbacks:
                try:
                    await cb(event)
                except Exception as e:
                    # TODO: логирование ошибок
                    print(f"[EventBus] Error in subscriber: {e}")

    async def start(self) -> None:
        if not self._task:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
