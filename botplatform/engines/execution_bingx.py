
from __future__ import annotations
from typing import List
from botplatform.core.models import OrderIntent, OrderUpdate
from botplatform.core.event_bus import EventBus
from botplatform.core.events import Event
from botplatform.exchanges.bingx.adapter import BingXExchangeAdapter

class BingXExecutionEngine:
    def __init__(self, event_bus: EventBus, exchange: BingXExchangeAdapter):
        self.event_bus = event_bus
        self.exchange = exchange

    async def submit(self, intents: List[OrderIntent]):
        for intent in intents:
            update = await self.exchange.place_order(intent)
            await self._publish(update)

    async def _publish(self, update: OrderUpdate):
        event = Event(
            type="order.update",
            timestamp=update.timestamp,
            source="BingXExecutionEngine",
            payload=update.dict()
        )
        await self.event_bus.publish(event)
