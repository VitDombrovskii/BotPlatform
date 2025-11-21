from __future__ import annotations

import time
from typing import List

from botplatform.core.context import StrategyContext
from botplatform.core.event_bus import EventBus
from botplatform.core.events import Event
from botplatform.core.models import (
    ActionIntent,
    MarketSnapshot,
    OrderIntent,
    OrderUpdate,
    PositionSnapshot,
)
from botplatform.engines.strategy import StrategyEngine
from botplatform.engines.execution_local import LocalExecutionEngine
from botplatform.exchanges.mock import MockExchange
from botplatform.strategies.hedge import HedgeStrategy


class StrategyRuntime:
    def __init__(
        self,
        event_bus: EventBus,
        exchange: MockExchange,
        symbols: List[str],
    ) -> None:
        self.event_bus = event_bus
        self.exchange = exchange
        self.symbols = symbols

        self.strategy_engine = StrategyEngine()
        if symbols:
            hedge = HedgeStrategy(symbol=symbols[0])
            self.strategy_engine.register_strategy(hedge)

        self.execution = LocalExecutionEngine(event_bus=self.event_bus, exchange=self.exchange)

        self.event_bus.subscribe("market.snapshot", self._on_market_event)
        self.event_bus.subscribe("order.update", self._on_order_event)

    async def _on_market_event(self, event: Event) -> None:
        snapshot = MarketSnapshot(**event.payload)
        positions = await self.exchange.get_positions([snapshot.symbol])
        position: PositionSnapshot | None = positions.get(snapshot.symbol)

        ctx = StrategyContext(
            symbol=snapshot.symbol,
            market=snapshot,
            signals=None,
            position=position,
            timestamp=snapshot.timestamp,
        )
        action_intents = self.strategy_engine.on_tick(ctx)
        order_intents = await self._build_order_intents(snapshot.symbol, action_intents, position)
        if order_intents:
            await self.execution.submit(order_intents)

    async def _on_order_event(self, event: Event) -> None:
        update = OrderUpdate(**event.payload)
        self.strategy_engine.on_order_update(update)

    async def _build_order_intents(
        self,
        symbol: str,
        action_intents: List[ActionIntent],
        position: PositionSnapshot | None,
    ) -> List[OrderIntent]:
        intents: List[OrderIntent] = []
        for ai in action_intents:
            if ai.action == "open" and ai.size and ai.side:
                side = "BUY" if ai.side == "LONG" else "SELL"
                client_id = f"{symbol}.{ai.side}.{int(time.time() * 1000)}"
                intents.append(
                    OrderIntent(
                        symbol=symbol,
                        side=side,
                        type="MARKET",
                        size=ai.size,
                        price=None,
                        client_id=client_id,
                        source="HedgeStrategy",
                        context=ai.context or {},
                    )
                )
            elif ai.action == "close" and ai.side and position and position.side == ai.side and position.size > 0:
                side = "SELL" if ai.side == "LONG" else "BUY"
                client_id = f"{symbol}.close.{int(time.time() * 1000)}"
                intents.append(
                    OrderIntent(
                        symbol=symbol,
                        side=side,
                        type="MARKET",
                        size=position.size,
                        price=None,
                        client_id=client_id,
                        source="HedgeStrategy",
                        context=ai.context or {},
                    )
                )
        return intents
