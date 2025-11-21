from __future__ import annotations

from typing import List

from botplatform.core.event_bus import EventBus
from botplatform.core.events import Event
from botplatform.core.models import OrderIntent, OrderUpdate
from botplatform.engines.execution import BaseExecutionEngine
from botplatform.exchanges.mock import MockExchange


class LocalExecutionEngine(BaseExecutionEngine):
    def __init__(self, event_bus: EventBus, exchange: MockExchange) -> None:
        self.event_bus = event_bus
        self.exchange = exchange

    async def submit(self, intents: List[OrderIntent]) -> None:
        for intent in intents:
            update = await self.exchange.place_order(intent)
            await self._publish(update)

    async def handle_update(self, update: OrderUpdate) -> None:
        await self._publish(update)

    async def _publish(self, update: OrderUpdate) -> None:
        event = Event(
            type="order.update",
            timestamp=update.timestamp,
            source="LocalExecutionEngine",
            payload=update.dict(),
        )
        await self.event_bus.publish(event)
