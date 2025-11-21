from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable, Optional

import websockets


class BingXWebSocket:
    """Простая обёртка над WebSocket BingX.

    На этом этапе:
    - подключается к ws_url
    - отправляет raw subscribe message
    - читает сообщения и передаёт их в handler

    Логика подписок (какие каналы, формат) должна быть уточнена по
    документации BingX. Здесь задаётся общий каркас.
    """

    def __init__(
        self,
        ws_url: str,
        subscribe_payload: Optional[dict] = None,
    ) -> None:
        self.ws_url = ws_url
        self.subscribe_payload = subscribe_payload or {}
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False

    async def run(self, handler: Callable[[dict], Awaitable[None]]) -> None:
        """Подключиться к WS и передавать сообщения в handler."""
        self._running = True
        async with websockets.connect(self.ws_url) as ws:
            if self.subscribe_payload:
                await ws.send(json.dumps(self.subscribe_payload))
            while self._running:
                msg = await ws.recv()
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    continue
                await handler(data)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
