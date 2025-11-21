from __future__ import annotations

from typing import List

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent, OrderUpdate
from botplatform.strategies.base import BaseStrategy
from botplatform.legs.long_leg import LongLeg
from botplatform.legs.short_leg import ShortLeg


class HedgeStrategy(BaseStrategy):
    def __init__(self, symbol: str, base_size: float = 0.001) -> None:
        super().__init__(name=f"hedge-{symbol}")
        self.symbol = symbol
        self.long_leg = LongLeg(name=f"{self.name}.long", base_size=base_size)
        self.short_leg = ShortLeg(name=f"{self.name}.short", base_size=base_size)

    def on_tick(self, ctx: StrategyContext) -> List[ActionIntent]:
        intents: List[ActionIntent] = []
        intents.extend(self.long_leg.on_tick(ctx))
        intents.extend(self.short_leg.on_tick(ctx))
        return intents

    def on_order_update(self, update: OrderUpdate) -> None:
        return
