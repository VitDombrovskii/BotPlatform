
from __future__ import annotations
from typing import Dict, List
from botplatform.core.models import MarketSnapshot, OrderIntent, OrderUpdate, PositionSnapshot
from botplatform.exchanges.bingx.rest import BingXRest

class BingXExchangeAdapter:
    def __init__(self, rest: BingXRest):
        self.rest = rest
        self.positions: Dict[str, PositionSnapshot] = {}

    async def get_market_snapshot(self, symbol: str) -> MarketSnapshot:
        price = self.rest.get_price(symbol)
        return MarketSnapshot(
            symbol=symbol,
            price=price,
            bid=price-0.5,
            ask=price+0.5,
            bids=[], asks=[], trades=[], timestamp=0
        )

    async def get_positions(self, symbols: List[str] | None = None):
        if symbols is None:
            return dict(self.positions)
        return {s: self.positions.get(s, PositionSnapshot(symbol=s)) for s in symbols}

    async def place_order(self, intent: OrderIntent) -> OrderUpdate:
        side = intent.side
        symbol = intent.symbol
        qty = intent.size
        price = intent.price
        resp = self.rest.place_order(symbol, side, qty, price)

        order_id = resp.get("data", {}).get("orderId", "unknown")
        avg_price = price or self.rest.get_price(symbol)

        pos = self.positions.get(symbol) or PositionSnapshot(symbol=symbol)
        if pos.side is None or pos.size == 0:
            pos.side = "LONG" if side == "BUY" else "SHORT"
            pos.size = qty
            pos.entry_price = avg_price
        else:
            # simplified PnL logic
            if pos.side == "LONG":
                if side == "BUY":
                    new_size = pos.size + qty
                    pos.entry_price = (pos.entry_price*pos.size + avg_price*qty)/new_size
                    pos.size = new_size
                else:
                    if qty >= pos.size:
                        pos.realized_pnl += (avg_price - pos.entry_price)*pos.size
                        pos.size = 0
                        pos.side = None
                    else:
                        pos.realized_pnl += (avg_price - pos.entry_price)*qty
                        pos.size -= qty
            elif pos.side == "SHORT":
                if side == "SELL":
                    new_size = pos.size + qty
                    pos.entry_price = (pos.entry_price*pos.size + avg_price*qty)/new_size
                    pos.size = new_size
                else:
                    if qty >= pos.size:
                        pos.realized_pnl += (pos.entry_price - avg_price)*pos.size
                        pos.size = 0
                        pos.side = None
                    else:
                        pos.realized_pnl += (pos.entry_price - avg_price)*qty
                        pos.size -= qty

        self.positions[symbol] = pos

        return OrderUpdate(
            order_id=order_id,
            client_id=intent.client_id,
            symbol=symbol,
            status="FILLED",
            filled_size=qty,
            remaining_size=0.0,
            avg_fill_price=avg_price,
            timestamp=0,
            raw=resp
        )

    async def cancel_order(self, order_id: str, symbol: str):
        return OrderUpdate(
            order_id=order_id,
            client_id="",
            symbol=symbol,
            status="CANCELLED",
            filled_size=0.0,
            remaining_size=0.0,
            avg_fill_price=None,
            timestamp=0,
            raw={"cancel": True}
        )
