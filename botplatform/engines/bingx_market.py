
from __future__ import annotations
import time
from typing import Optional, List
from botplatform.exchanges.bingx.websocket import BingXWebSocket
from botplatform.core.event_bus import EventBus
from botplatform.core.events import Event
from botplatform.core.models import MarketSnapshot, OrderBookLevel, Trade

class BingXMarketEngine:
    def __init__(self, event_bus: EventBus, ws_url: str, symbols: List[str]):
        self.event_bus = event_bus
        self.ws_url = ws_url
        self.symbols = symbols
        self.ws = BingXWebSocket(
            ws_url,
            {"op": "subscribe", "args": [f"swap/ticker:{s}" for s in symbols]}
        )

    async def start(self):
        await self.ws.run(self._on_msg)

    async def stop(self):
        await self.ws.stop()

    async def _on_msg(self, msg: dict):
        snap = self._to_snapshot(msg)
        if snap:
            event = Event(
                type="market.snapshot",
                timestamp=snap.timestamp,
                source="BingXMarketEngine",
                payload=snap.dict()
            )
            await self.event_bus.publish(event)

    def _to_snapshot(self, msg: dict) -> Optional[MarketSnapshot]:
        data = msg.get("data")
        if not data:
            return None

        symbol = data.get("symbol")
        if not symbol:
            return None

        price = float(data.get("lastPrice", 0))
        bid = float(data.get("bidPrice", price))
        ask = float(data.get("askPrice", price))

        ts = int(data.get("timestamp", time.time()*1000))

        return MarketSnapshot(
            symbol=symbol,
            price=price,
            bid=bid,
            ask=ask,
            bids=[OrderBookLevel(price=bid, size=0)],
            asks=[OrderBookLevel(price=ask, size=0)],
            trades=[Trade(price=price, size=0, side="BUY", timestamp=ts)],
            timestamp=ts
        )
