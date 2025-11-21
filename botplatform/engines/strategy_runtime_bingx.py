
from __future__ import annotations
import time
from typing import List
from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent, OrderIntent, OrderUpdate, MarketSnapshot
from botplatform.engines.execution_bingx import BingXExecutionEngine
from botplatform.core.event_bus import EventBus
from botplatform.core.events import Event
from botplatform.strategies.hedge import HedgeStrategy
from botplatform.exchanges.bingx.adapter import BingXExchangeAdapter
from botplatform.engines.strategy import StrategyEngine

class BingXStrategyRuntime:
    def __init__(self, event_bus: EventBus, exchange: BingXExchangeAdapter, symbols: List[str]):
        self.event_bus = event_bus
        self.exchange = exchange
        self.symbols = symbols

        self.strategy_engine = StrategyEngine()
        self.strategy_engine.register_strategy(HedgeStrategy(symbols[0]))

        self.execution = BingXExecutionEngine(event_bus, exchange)

        self.event_bus.subscribe("market.snapshot", self._on_market)
        self.event_bus.subscribe("order.update", self._on_order)

    async def _on_market(self, event: Event):
        snap = MarketSnapshot(**event.payload)
        positions = await self.exchange.get_positions([snap.symbol])
        pos = positions.get(snap.symbol)

        ctx = StrategyContext(
            symbol=snap.symbol,
            market=snap,
            signals=None,
            position=pos,
            timestamp=snap.timestamp
        )
        actions = self.strategy_engine.on_tick(ctx)
        intents = await self._actions_to_orders(snap.symbol, actions, pos)
        if intents:
            await self.execution.submit(intents)

    async def _on_order(self, event: Event):
        update = OrderUpdate(**event.payload)
        self.strategy_engine.on_order_update(update)

    async def _actions_to_orders(self, symbol, actions, pos):
        out = []
        for a in actions:
            if a.action == "open" and a.side and a.size:
                side = "BUY" if a.side == "LONG" else "SELL"
                cid = f"{symbol}.{side}.{int(time.time()*1000)}"
                out.append(OrderIntent(symbol, side, "MARKET", a.size, None, cid, "HedgeStrategy", {}))
        return out
