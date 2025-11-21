from __future__ import annotations

import asyncio
import math
import random
import time
from typing import List

from botplatform.core.event_bus import EventBus
from botplatform.core.events import Event
from botplatform.core.models import MarketSnapshot, OrderBookLevel, Trade


class FakeMarketEngine:
    def __init__(
        self,
        event_bus: EventBus,
        symbols: List[str],
        interval_ms: int = 500,
        mode: str = "sine",
    ) -> None:
        self.event_bus = event_bus
        self.symbols = symbols
        self.interval_ms = interval_ms
        self.mode = mode
        self._running: bool = False
        self._task: asyncio.Task | None = None
        self._t: float = 0.0

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    def _generate_price(self) -> float:
        if self.mode == "sine":
            self._t += 0.1
            return 100.0 + math.sin(self._t) * 5.0
        return 100.0 + random.uniform(-1.0, 1.0)

    async def _run(self) -> None:
        while self._running:
            await asyncio.sleep(self.interval_ms / 1000.0)
            for symbol in self.symbols:
                price = self._generate_price()
                ts = int(time.time() * 1000)
                snapshot = MarketSnapshot(
                    symbol=symbol,
                    price=price,
                    bid=price - 0.5,
                    ask=price + 0.5,
                    bids=[OrderBookLevel(price=price - 0.5, size=1.0)],
                    asks=[OrderBookLevel(price=price + 0.5, size=1.0)],
                    trades=[Trade(price=price, size=0.1, side="BUY", timestamp=ts)],
                    timestamp=ts,
                )
                event = Event(
                    type="market.snapshot",
                    timestamp=ts,
                    source="FakeMarketEngine",
                    payload=snapshot.dict(),
                )
                await self.event_bus.publish(event)
