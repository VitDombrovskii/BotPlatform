from __future__ import annotations

from typing import Dict, List

from botplatform.core.models import (
    MarketSnapshot,
    OrderIntent,
    OrderUpdate,
    PositionSnapshot,
)
from botplatform.exchanges.bingx.rest import BingXRest


class BingXExchangeAdapter:
    """Адаптер BingX под интерфейс Exchange.

    На этом этапе использует только REST-клиент:
    - get_market_snapshot
    - place_order
    - get_positions (пока in-memory карта)

    В будущем сюда будет добавлен WebSocket для:
    - стриминга маркет-данных
    - стриминга order updates
    """

    def __init__(self, rest: BingXRest) -> None:
        self.rest = rest
        self._positions: Dict[str, PositionSnapshot] = {}

    async def get_market_snapshot(self, symbol: str) -> MarketSnapshot:
        price = self.rest.get_price(symbol)
        # Пока bid/ask не берём из API, а строим искусственно
        return MarketSnapshot(
            symbol=symbol,
            price=price,
            bid=price - 0.5,
            ask=price + 0.5,
            bids=[],
            asks=[],
            trades=[],
            timestamp=0,
        )

    async def get_positions(
        self,
        symbols: List[str] | None = None,
    ) -> Dict[str, PositionSnapshot]:
        # TODO: привязать к реальному эндпоинту BingX по позициям.
        if symbols is None:
            return dict(self._positions)
        return {s: self._positions[s] for s in symbols if s in self._positions}

    async def place_order(self, intent: OrderIntent) -> OrderUpdate:
        side = intent.side  # BUY / SELL
        symbol = intent.symbol
        qty = intent.size
        price = intent.price
        order_type = intent.type

        resp = self.rest.place_order(
            symbol=symbol,
            side=side,
            quantity=qty,
            price=price,
            order_type=order_type,
        )
        data = resp.get("data", {}) if isinstance(resp, dict) else {}
        order_id = data.get("orderId") or data.get("order_id") or "unknown"

        avg_price = price
        if avg_price is None:
            try:
                avg_price = float(data.get("avgPrice") or data.get("price") or 0.0)
            except Exception:
                avg_price = 0.0

        # Локальное обновление позиций (пока по простой модели, аналогично MockExchange)
        pos = self._positions.get(symbol) or PositionSnapshot(symbol=symbol)
        if pos.side is None or pos.size == 0:
            pos.side = "LONG" if side == "BUY" else "SHORT"
            pos.size = qty
            pos.entry_price = avg_price
        else:
            # Упрощённая логика, в реальной реализации стоит вынести в общий PositionEngine
            if pos.side == "LONG":
                if side == "BUY":
                    new_size = pos.size + qty
                    pos.entry_price = (pos.entry_price * pos.size + avg_price * qty) / new_size
                    pos.size = new_size
                else:
                    if qty < pos.size:
                        closed = qty
                        pos.realized_pnl += (avg_price - pos.entry_price) * closed
                        pos.size -= closed
                    elif qty == pos.size:
                        closed = qty
                        pos.realized_pnl += (avg_price - pos.entry_price) * closed
                        pos.size = 0.0
                        pos.side = None
                        pos.entry_price = 0.0
                    else:
                        closed = pos.size
                        pos.realized_pnl += (avg_price - pos.entry_price) * closed
                        new_short = qty - closed
                        pos.side = "SHORT"
                        pos.size = new_short
                        pos.entry_price = avg_price
            elif pos.side == "SHORT":
                if side == "SELL":
                    new_size = pos.size + qty
                    pos.entry_price = (pos.entry_price * pos.size + avg_price * qty) / new_size
                    pos.size = new_size
                else:
                    if qty < pos.size:
                        closed = qty
                        pos.realized_pnl += (pos.entry_price - avg_price) * closed
                        pos.size -= closed
                    elif qty == pos.size:
                        closed = qty
                        pos.realized_pnl += (pos.entry_price - avg_price) * closed
                        pos.size = 0.0
                        pos.side = None
                        pos.entry_price = 0.0
                    else:
                        closed = pos.size
                        pos.realized_pnl += (pos.entry_price - avg_price) * closed
                        new_long = qty - closed
                        pos.side = "LONG"
                        pos.size = new_long
                        pos.entry_price = avg_price

        self._positions[symbol] = pos

        update = OrderUpdate(
            order_id=order_id,
            client_id=intent.client_id,
            symbol=symbol,
            status="FILLED",  # Предполагаем немедленное исполнение, пока без частичных
            filled_size=qty,
            remaining_size=0.0,
            avg_fill_price=avg_price,
            timestamp=0,
            raw=resp if isinstance(resp, dict) else {"raw": resp},
        )
        return update

    async def cancel_order(self, order_id: str, symbol: str) -> OrderUpdate:
        # TODO: реализовать реальный вызов cancel на BingX
        return OrderUpdate(
            order_id=order_id,
            client_id="",
            symbol=symbol,
            status="CANCELLED",
            filled_size=0.0,
            remaining_size=0.0,
            avg_fill_price=None,
            timestamp=0,
            raw={"status": "cancelled", "exchange": "bingx"},
        )
