# botplatform/exchanges/mock.py

from __future__ import annotations

import time
from typing import Dict, List, Callable, Awaitable

from botplatform.core.models import (
    MarketSnapshot,
    PositionSnapshot,
    OrderIntent,
    OrderUpdate,
)
from botplatform.exchanges.base import Exchange


class MockExchange:
    """Простой симулятор биржи для локальных тестов.

    Возможности:
    - принимает OrderIntent и сразу исполняет их как полностью FILLED,
    - обновляет внутреннее состояние позиций (PositionSnapshot),
    - возвращает OrderUpdate с avg_fill_price,
    - может использовать внешний провайдер цены (price_provider).

    Это не точный matching engine, а удобный инструмент для
    отладки стратегий и ExecutionEngine без реальной биржи.
    """

    def __init__(self, price_provider: Callable[[str], float] | None = None) -> None:
        # Хранение позиций по символу
        self._positions: Dict[str, PositionSnapshot] = {}
        # Счётчик для order_id
        self._order_seq: int = 0
        # Провайдер текущей цены (например, FakeMarketEngine через замыкание)
        self._price_provider = price_provider or (lambda symbol: 100.0)

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    def _next_order_id(self) -> str:
        self._order_seq += 1
        return f"mock-order-{self._order_seq}"

    def _get_position(self, symbol: str) -> PositionSnapshot:
        if symbol not in self._positions:
            self._positions[symbol] = PositionSnapshot(symbol=symbol)
        return self._positions[symbol]

    def _apply_fill(self, symbol: str, side: str, size: float, price: float) -> None:
        """Обновление позиции по факту исполнения ордера.

        Реализует логику из 24-position-model.md:
        - при наращивании позиции пересчитывает entry_price,
        - при сокращении считает realized_pnl,
        - unrealized_pnl не считается здесь (это делает MarketEngine/отдельный модуль).
        """

        pos = self._get_position(symbol)

        # BUY увеличивает LONG или уменьшает SHORT
        # SELL увеличивает SHORT или уменьшает LONG
        if pos.side is None or pos.size == 0:
            # Открытие новой позиции
            if side == "BUY":
                pos.side = "LONG"
                pos.size = size
                pos.entry_price = price
            else:  # "SELL"
                pos.side = "SHORT"
                pos.size = size
                pos.entry_price = price
            return

        if pos.side == "LONG":
            if side == "BUY":
                # Увеличение LONG (scale-in)
                new_size = pos.size + size
                pos.entry_price = (pos.entry_price * pos.size + price * size) / new_size
                pos.size = new_size
            else:  # SELL против LONG
                if size < pos.size:
                    # Частичное закрытие LONG
                    closed_size = size
                    pos.realized_pnl += (price - pos.entry_price) * closed_size
                    pos.size -= closed_size
                elif size == pos.size:
                    # Полное закрытие
                    closed_size = size
                    pos.realized_pnl += (price - pos.entry_price) * closed_size
                    pos.size = 0
                    pos.side = None
                    pos.entry_price = 0.0
                else:
                    # Переворот позиции: закрыли LONG и открыли SHORT
                    closed_size = pos.size
                    pos.realized_pnl += (price - pos.entry_price) * closed_size
                    new_short_size = size - closed_size
                    pos.side = "SHORT"
                    pos.size = new_short_size
                    pos.entry_price = price

        elif pos.side == "SHORT":
            if side == "SELL":
                # Увеличение SHORT (scale-in)
                new_size = pos.size + size
                pos.entry_price = (pos.entry_price * pos.size + price * size) / new_size
                pos.size = new_size
            else:  # BUY против SHORT
                if size < pos.size:
                    # Частичное закрытие SHORT
                    closed_size = size
                    pos.realized_pnl += (pos.entry_price - price) * closed_size
                    pos.size -= closed_size
                elif size == pos.size:
                    # Полное закрытие
                    closed_size = size
                    pos.realized_pnl += (pos.entry_price - price) * closed_size
                    pos.size = 0
                    pos.side = None
                    pos.entry_price = 0.0
                else:
                    # Переворот позиции: закрыли SHORT и открыли LONG
                    closed_size = pos.size
                    pos.realized_pnl += (pos.entry_price - price) * closed_size
                    new_long_size = size - closed_size
                    pos.side = "LONG"
                    pos.size = new_long_size
                    pos.entry_price = price

    # ------------------------------------------------------------------
    # Реализация протокола Exchange (минимальная)
    # ------------------------------------------------------------------

    async def get_market_snapshot(self, symbol: str) -> MarketSnapshot:
        """Возвращает простой MarketSnapshot по текущей цене.

        Используется только для тестов; реальный MarketEngine обычно
        снабжает стратегию данными лучше.
        """
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
        """Симулирует немедленное полное исполнение ордера."""
        symbol = intent.symbol
        price = intent.price or self._price_provider(symbol)
        size = intent.size
        ts = int(time.time() * 1000)

        # Обновляем внутреннюю позицию
        self._apply_fill(symbol=symbol, side=intent.side, size=size, price=price)

        order_id = self._next_order_id()
        update = OrderUpdate(
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
        return update

    async def cancel_order(self, order_id: str, symbol: str) -> OrderUpdate:
        """В MockExchange отмена ордера просто возвращает CANCELLED без эффекта."""
        ts = int(time.time() * 1000)
        update = OrderUpdate(
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
        return update

    async def stream_market_data(
        self,
        symbols: List[str],
        callback: Callable[[MarketSnapshot], Awaitable[None]],
    ) -> None:
        """Для совместимости с протоколом. В тестах можно не использовать."""
        raise NotImplementedError("MockExchange.stream_market_data не реализован")

    async def stream_order_updates(
        self,
        callback: Callable[[OrderUpdate], Awaitable[None]],
    ) -> None:
        """Для совместимости с протоколом. MockExchange отдаёт update напрямую из place_order."""
        raise NotImplementedError("MockExchange.stream_order_updates не реализован")
