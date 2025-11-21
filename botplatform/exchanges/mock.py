from __future__ import annotations

import time
from typing import Callable, Dict, List

from botplatform.core.models import (
    MarketSnapshot,
    OrderIntent,
    OrderUpdate,
    PositionSnapshot,
)


class MockExchange:
    def __init__(self, price_provider: Callable[[str], float] | None = None) -> None:
        self._positions: Dict[str, PositionSnapshot] = {}
        self._order_seq: int = 0
        self._price_provider = price_provider or (lambda symbol: 100.0)

    def _next_order_id(self) -> str:
        self._order_seq += 1
        return f"mock-order-{self._order_seq}"

    def _get_position(self, symbol: str) -> PositionSnapshot:
        if symbol not in self._positions:
            self._positions[symbol] = PositionSnapshot(symbol=symbol)
        return self._positions[symbol]

    def _apply_fill(self, symbol: str, side: str, size: float, price: float) -> None:
        pos = self._get_position(symbol)

        if pos.side is None or pos.size == 0:
            if side == "BUY":
                pos.side = "LONG"
            else:
                pos.side = "SHORT"
            pos.size = size
            pos.entry_price = price
            return

        if pos.side == "LONG":
            if side == "BUY":
                new_size = pos.size + size
                pos.entry_price = (pos.entry_price * pos.size + price * size) / new_size
                pos.size = new_size
            else:
                if size < pos.size:
                    closed = size
                    pos.realized_pnl += (price - pos.entry_price) * closed
                    pos.size -= closed
                elif size == pos.size:
                    closed = size
                    pos.realized_pnl += (price - pos.entry_price) * closed
                    pos.size = 0.0
                    pos.side = None
                    pos.entry_price = 0.0
                else:
                    closed = pos.size
                    pos.realized_pnl += (price - pos.entry_price) * closed
                    new_short = size - closed
                    pos.side = "SHORT"
                    pos.size = new_short
                    pos.entry_price = price

        elif pos.side == "SHORT":
            if side == "SELL":
                new_size = pos.size + size
                pos.entry_price = (pos.entry_price * pos.size + price * size) / new_size
                pos.size = new_size
            else:
                if size < pos.size:
                    closed = size
                    pos.realized_pnl += (pos.entry_price - price) * closed
                    pos.size -= closed
                elif size == pos.size:
                    closed = size
                    pos.realized_pnl += (pos.entry_price - price) * closed
                    pos.size = 0.0
                    pos.side = None
                    pos.entry_price = 0.0
                else:
                    closed = pos.size
                    pos.realized_pnl += (pos.entry_price - price) * closed
                    new_long = size - closed
                    pos.side = "LONG"
                    pos.size = new_long
                    pos.entry_price = price

    async def get_market_snapshot(self, symbol: str) -> MarketSnapshot:
        price = self._price_provider(symbol)
        ts = int(time.time() * 1000)
        return MarketSnapshot(
            symbol=symbol,
            price=price,
            bid=price - 0.5,
            ask=price + 0.5,
            bids=[],
            asks=[],
            trades=[],
            timestamp=ts,
        )

    async def get_positions(self, symbols: List[str] | None = None) -> Dict[str, PositionSnapshot]:
        if symbols is None:
            return dict(self._positions)
        return {s: self._get_position(s) for s in symbols}

    async def place_order(self, intent: OrderIntent) -> OrderUpdate:
        symbol = intent.symbol
        price = intent.price or self._price_provider(symbol)
        size = intent.size
        ts = int(time.time() * 1000)

        self._apply_fill(symbol=symbol, side=intent.side, size=size, price=price)

        order_id = self._next_order_id()
        return OrderUpdate(
            order_id=order_id,
            client_id=intent.client_id,
            symbol=symbol,
            status="FILLED",
            filled_size=size,
            remaining_size=0.0,
            avg_fill_price=price,
            timestamp=ts,
            raw={"mock": True},
        )

    async def cancel_order(self, order_id: str, symbol: str) -> OrderUpdate:
        ts = int(time.time() * 1000)
        return OrderUpdate(
            order_id=order_id,
            client_id="",
            symbol=symbol,
            status="CANCELLED",
            filled_size=0.0,
            remaining_size=0.0,
            avg_fill_price=None,
            timestamp=ts,
            raw={"mock": True, "reason": "cancelled"},
        )
