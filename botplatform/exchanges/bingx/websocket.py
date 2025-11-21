
from __future__ import annotations
import asyncio, json, websockets
from typing import Awaitable, Callable

class BingXWebSocket:
    def __init__(self, ws_url: str, subscribe_payload: dict):
        self.ws_url = ws_url
        self.payload = subscribe_payload
        self._running = False

    async def run(self, handler: Callable[[dict], Awaitable[None]]):
        self._running = True
        async with websockets.connect(self.ws_url) as ws:
            await ws.send(json.dumps(self.payload))
            while self._running:
                msg = await ws.recv()
                try:
                    data = json.loads(msg)
                    await handler(data)
                except:
                    continue

    async def stop(self):
        self._running = False
