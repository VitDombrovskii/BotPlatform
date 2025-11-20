from __future__ import annotations

from typing import Protocol, List, Callable, Awaitable, Dict

from botplatform.core.models import MarketSnapshot, PositionSnapshot, OrderIntent, OrderUpdate


class Exchange(Protocol):
    """
    Унифицированный интерфейс биржевого адаптера.

    Реализации (Binance, BingX, OKX и т.д.) должны соответствовать этому протоколу.
    """

    async def get_market_snapshot(self, symbol: str) -> MarketSnapshot:
        ...

    async def get_positions(self, symbols: List[str] | None = None) -> Dict[str, PositionSnapshot]:
        ...

    async def place_order(self, intent: OrderIntent) -> OrderUpdate:
        ...

    async def cancel_order(self, order_id: str, symbol: str) -> OrderUpdate:
        ...

    async def stream_market_data(
        self,
        symbols: List[str],
        callback: Callable[[MarketSnapshot], Awaitable[None]],
    ) -> None:
        ...

    async def stream_order_updates(
        self,
        callback: Callable[[OrderUpdate], Awaitable[None]],
    ) -> None:
        ...
